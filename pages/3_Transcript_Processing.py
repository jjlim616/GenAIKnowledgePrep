# pages/3_Transcript_Processing.py
# Core Python modules
import os
from datetime import datetime

# Streamlit
import streamlit as st

from src.utils import (
    initialize_session,
    update_activity_timestamp,
    check_session_expiry,
)
from src.prompts import (
    SUMMARY_DEFAULT_SYSTEM_PROMPT,
    URS_SUMMARY_PROMPT,
    GENERAL_MEETING_PROMPT,
    OVERVIEW_SUMMARY_PROMPT
)
from src.text_processor import (
    summarize_transcription,
    export_summary_to_docx,
    extract_text_from_docx,
    extract_text_from_pdf,
)

# Page configuration and layout
st.set_page_config(
    page_title="Transcript Processing",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Centered Title and Subheader
st.title("📝 Transcript Processing & Summaries", anchor=False)
st.caption("Transform your meeting transcripts into concise, actionable summaries.")
st.divider()

# Define available models
AVAILABLE_MODELS = {
    "OpenAI GPT-4.1": "gpt-4.1",
    "Grok-3": "grok-3",
    "Grok-3-mini": "grok-3-mini",
    "Gemini 2.0 Flash": "gemini-2.0-flash",
    "Gemini 2.5 Pro (Exp)": "gemini-2.5-pro-exp-03-25",
    "Gemini 1.5 Pro Latest": "gemini-1.5-pro-latest",
    "OpenAI o4-Mini": "o4-mini"
}

# Initialize session and check for expiry
initialize_session()
if not check_session_expiry(max_inactivity_days=1):
    st.warning("Session has expired due to inactivity. Starting a new session.")
    initialize_session()
update_activity_timestamp()

# Initialize session state variables
for key in ["loaded_transcript_text", "selected_prompt_key", "selected_prompt", "transcript_summary", "transcript_reasoning", "exported_summary_path", "current_page"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "current_page" else 1
        if key == "selected_prompt_key":
            st.session_state[key] = "default"

# Prompt Templates
PROMPT_TEMPLATES = {
    "default": {"name": "Technical Focus", "icon": "🔍", "description": "Focuses on technical requirements, action items, and clarifications for URS/SRS/SDS meetings.", "prompt": SUMMARY_DEFAULT_SYSTEM_PROMPT},
    "urs": {"name": "Detailed Requirements", "icon": "📋", "description": "Deep analysis of user requirements with prioritization and dependency tracking.", "prompt": URS_SUMMARY_PROMPT},
    "general": {"name": "General Meeting", "icon": "🗣️", "description": "Summarizes general meetings with focus on decisions, action items, and discussion points.", "prompt": GENERAL_MEETING_PROMPT},
    "overview": {"name": "Executive Overview", "icon": "👔", "description": "Provides a high-level summary suitable for executive stakeholders.", "prompt": OVERVIEW_SUMMARY_PROMPT}
}

# Main container
main_container = st.container(border=False)

with main_container:
    # Step 1: Upload Transcript
    with st.container(border=True):
        st.subheader("1️⃣ Upload Transcript Document")
        uploaded_file = st.file_uploader(
            "Upload a transcript (DOCX or PDF):",
            type=["docx", "pdf"],
            key="doc_transcript_uploader",
            label_visibility="collapsed",
            help="Maximum file size: 200MB"
        )

        if uploaded_file:
            st.session_state.uploaded_filename = uploaded_file.name
            try:
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                file_bytes = uploaded_file.getvalue()
                transcript_text = None
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    if file_extension == ".docx":
                        transcript_text = extract_text_from_docx(file_bytes)
                    elif file_extension == ".pdf":
                        transcript_text = extract_text_from_pdf(file_bytes)
                    else:
                        st.error("Unsupported file format.")
                if transcript_text:
                    if transcript_text != st.session_state.get("loaded_transcript_text"):
                        st.session_state.loaded_transcript_text = transcript_text
                        st.session_state.transcript_summary = None
                        st.session_state.transcript_reasoning = None
                        st.session_state.exported_summary_path = None
                        st.session_state.current_page = 1
                        st.success(f"✅ Successfully loaded and processed: {uploaded_file.name}")
                else:
                    st.session_state.loaded_transcript_text = None
                    st.session_state.transcript_summary = None
                    st.session_state.transcript_reasoning = None
            except Exception as e:
                st.error(f"Error processing transcript document: {e}")
                st.session_state.loaded_transcript_text = None
                st.session_state.transcript_summary = None
                st.session_state.transcript_reasoning = None

        if st.session_state.get("loaded_transcript_text"):
            with st.expander("Preview Transcript", expanded=False):
                st.text(st.session_state.loaded_transcript_text[:1000] + "..." if len(st.session_state.loaded_transcript_text) > 1000 else st.session_state.loaded_transcript_text)

    st.write("")

    # Step 2: Configure Summary Generation
    with st.container(border=True):
        st.subheader("2️⃣ Configure Summary")
        selected_model = st.selectbox(
            "Select AI Model:",
            options=list(AVAILABLE_MODELS.keys()),
            index=list(AVAILABLE_MODELS.values()).index("gemini-1.5-pro-latest"),
            format_func=lambda x: x,
            help="Choose the AI model for generating the summary."
        )
        model_id = AVAILABLE_MODELS[selected_model]

        # Reasoning checkbox for supported models
        enable_reasoning = False
        if model_id in ["grok-3-mini", "gemini-2.5-pro-exp-03-25", "o4-mini"]:
            enable_reasoning = st.checkbox(
                f"Enable Reasoning Mode ({selected_model})",
                value=False,
                key="reasoning_mode",
                help="Show step-by-step reasoning before the summary (available for Grok-3-mini and Gemini 2.5 Pro)."
            )

        st.divider()

        prompt_options = list(PROMPT_TEMPLATES.keys())
        st.session_state.selected_prompt_key = st.radio(
            "Select Summary Template:",
            prompt_options,
            format_func=lambda x: f"{PROMPT_TEMPLATES[x]['icon']} {PROMPT_TEMPLATES[x]['name']}",
            key="summary_template_radio",
            horizontal=True,
            index=prompt_options.index(st.session_state.get("selected_prompt_key", "default"))
        )

        st.info(PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["description"])

        view_prompt_enabled = st.checkbox("View prompt template")
        if view_prompt_enabled:
            with st.expander("Selected Prompt Template", expanded=True):
                st.text_area(
                    "Prompt Template:",
                    value=PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["prompt"],
                    height=400,
                    disabled=True,
                    help="This is the prompt template used for generating the summary."
                )

        additional_focus = st.text_area(
            "Additional Focus Instructions (Optional):",
            placeholder="E.g., 'Focus on budget discussions', 'Highlight security concerns mentioned by John Doe', 'Extract all questions raised'",
            height=100,
            key="additional_focus_text",
            help="Provide specific keywords or topics for the AI to pay extra attention to."
        )

    st.write("")

    # Step 3: Generate Summary
    generate_button = st.button(
        "🚀 Generate Summary",
        key="generate_summary_button",
        disabled=not st.session_state.get("loaded_transcript_text"),
        help="Upload a transcript document first to enable generation.",
        use_container_width=True
    )

    if generate_button and st.session_state.get("loaded_transcript_text"):
        try:
            st.session_state.selected_prompt = PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["prompt"]
            final_prompt = st.session_state.selected_prompt
            if additional_focus:
                final_prompt += f"\n\n--- Additional Focus Instructions ---\n{additional_focus}"
            with st.spinner(f"⏳ Generating summary using {selected_model}... This may take a moment."):
                summary, reasoning = summarize_transcription(
                    st.session_state.loaded_transcript_text,
                    model=model_id,
                    custom_prompt=final_prompt,
                    enable_reasoning=enable_reasoning
                )
            st.session_state.transcript_summary = summary
            st.session_state.transcript_reasoning = reasoning
            st.session_state.current_page = 1
            st.session_state.exported_summary_path = None
            st.success("🎉 Summary generated successfully!")
        except Exception as e:
            st.error(f"❌ Error generating summary: {e}")
            st.session_state.transcript_summary = None
            st.session_state.transcript_reasoning = None

    st.write("")

    # Step 4: Display Summary and Reasoning (if generated)
    if st.session_state.get("transcript_summary"):
        st.divider()
        st.subheader("📊 Generated Summary")
        
        # Display reasoning if available
        if st.session_state.get("transcript_reasoning") and enable_reasoning:
            with st.container(border=True):
                st.write("**Reasoning Process**")
                st.markdown(st.session_state.transcript_reasoning)

        with st.container(border=True, height=600):
            st.markdown(st.session_state.transcript_summary)

        st.write("")

        # Step 5: Export Options
        with st.container(border=True):
            st.subheader("💾 Export Summary")
            base_transcript_dir = "transcripts"
            try:
                if not os.path.exists(base_transcript_dir):
                    os.makedirs(base_transcript_dir)
                existing_folders = [d for d in os.listdir(base_transcript_dir) if os.path.isdir(os.path.join(base_transcript_dir, d))]
            except Exception as e:
                st.warning(f"Error accessing transcript folders: {e}")
                existing_folders = []
            existing_folders.sort()
            folder_options = ["Create New Folder"] + existing_folders

            col_folder1, col_folder2 = st.columns([2, 3])
            with col_folder1:
                selected_folder_option = st.selectbox("Select/Create Folder:", folder_options, key="folder_select_plain")
            output_folder = base_transcript_dir
            with col_folder2:
                if selected_folder_option == "Create New Folder":
                    new_folder_name = st.text_input("New folder name:", key="new_folder_name_plain")
                    if new_folder_name:
                        safe_folder_name = "".join(c for c in new_folder_name if c.isalnum() or c in ('_', '-')).strip()
                        if safe_folder_name:
                            output_folder = os.path.join(base_transcript_dir, safe_folder_name)
                        else:
                            st.warning("Invalid folder name.")
                else:
                    output_folder = os.path.join(base_transcript_dir, selected_folder_option)

            selected_template_name = PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["name"].replace(" ", "_")
            default_filename = f"{selected_template_name}_summary_{datetime.now().strftime('%Y%m%d_%H%M')}"
            export_file_name = st.text_input("File name (no extension):", value=default_filename, key="export_filename_plain")
            safe_export_file_name = "".join(c for c in export_file_name if c.isalnum() or c in ('_', '-')).strip() or "summary_export"

            st.write("")
            col_fmt1, col_fmt2 = st.columns(2)
            export_triggered = False
            export_format = None
            with col_fmt1:
                if st.button("📄 Export as DOCX", key="fmt_docx_plain", use_container_width=True):
                    export_triggered = True
                    export_format = "DOCX"
            with col_fmt2:
                if st.button("📝 Export as Markdown", key="fmt_md_plain", use_container_width=True):
                    export_triggered = True
                    export_format = "Markdown"

            if export_triggered and export_format:
                try:
                    if not os.path.exists(output_folder):
                        os.makedirs(output_folder)
                        st.info(f"Created folder: {output_folder}")
                    with st.spinner(f"Exporting summary to {export_format}..."):
                        if export_format == "DOCX":
                            summary_file_name = f"{safe_export_file_name}.docx"
                            summary_content = st.session_state.transcript_summary
                            if st.session_state.transcript_reasoning and enable_reasoning:
                                summary_content = f"# Reasoning Process\n\n{st.session_state.transcript_reasoning}\n\n# Meeting Summary\n\n{summary_content}"
                            summary_path = export_summary_to_docx(summary_content, output_folder=output_folder, file_name=summary_file_name)
                        else:  # Markdown
                            summary_file_name = f"{safe_export_file_name}.md"
                            summary_path = os.path.join(output_folder, summary_file_name)
                            summary_content = st.session_state.transcript_summary
                            if st.session_state.transcript_reasoning and enable_reasoning:
                                summary_content = f"# Reasoning Process\n\n{st.session_state.transcript_reasoning}\n\n# Meeting Summary\n\n{summary_content}"
                            with open(summary_path, "w", encoding="utf-8") as f:
                                f.write(f"---\ntitle: {safe_export_file_name}\ndate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n---\n\n{summary_content}")
                        st.session_state.exported_summary_path = summary_path
                        st.success(f"✅ Summary exported successfully to: `{summary_path}`")
                except Exception as e:
                    st.error(f"❌ Error exporting summary: {e}")
                    st.session_state.exported_summary_path = None

            # Download Button
            if st.session_state.get("exported_summary_path") and os.path.exists(st.session_state.exported_summary_path):
                st.write("")
                file_path = st.session_state.exported_summary_path
                file_name = os.path.basename(file_path)
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if file_path.endswith(".docx") else "text/markdown"
                icon = "📄" if file_path.endswith(".docx") else "📝"
                try:
                    with open(file_path, "rb") as file:
                        st.download_button(
                            label=f"{icon} Download '{file_name}'",
                            data=file,
                            file_name=file_name,
                            mime=mime_type,
                            key="download_plain",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Error preparing download: {e}")

    # Placeholders
    elif not st.session_state.get("loaded_transcript_text"):
        st.info("⬆️ Upload a transcript document (DOCX or PDF) to get started.")
    elif st.session_state.get("loaded_transcript_text") and not st.session_state.get("transcript_summary"):
        st.info("⚙️ Configure the summary options above and click 'Generate Summary'.")

# Footer
st.divider()
with st.expander("💡 Tips for Better Summaries"):
    st.markdown("""
    *   **Choose the right template:** Match the template (Technical, Requirements, General, Overview) to your meeting's primary purpose.
    *   **Use 'Additional Focus':** Guide the AI by listing specific names, projects, keywords, or types of information (e.g., 'all decisions made', 'budget concerns', 'tasks assigned to Sarah').
    *   **Enable Reasoning:** For Grok-3-mini or Gemini 2.5 Pro, enable reasoning to see the AI's thought process before the summary.
    *   **PDF Quality Matters:** Ensure your PDF contains selectable text, not just images of text, for reliable extraction.
    *   **Review & Refine:** AI summaries are a great starting point. Always review for accuracy and completeness, especially for critical information.
    """)