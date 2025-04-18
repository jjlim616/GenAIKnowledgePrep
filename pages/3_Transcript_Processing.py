# pages/3_Transcript_ProcessingV2.py
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
    layout="wide", # Keep wide layout
    initial_sidebar_state="expanded"
)

# Centered Title and Subheader using Streamlit elements
st.title("📝 Transcript Processing & Summaries", anchor=False)
st.caption("Transform your meeting transcripts into concise, actionable summaries.")
st.divider() # Add a visual separator early on

# Define available Gemini models
AVAILABLE_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-pro-exp-03-25",
    "gemini-1.5-pro-latest"
]

# Initialize session and check for expiry
initialize_session()
if not check_session_expiry(max_inactivity_days=1):
    st.warning("Session has expired due to inactivity. Starting a new session.")
    initialize_session()
update_activity_timestamp()

# Initialize session state variables
for key in ["loaded_transcript_text", "selected_prompt_key", "selected_prompt", "transcript_summary", "exported_summary_path", "current_page"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "current_page" else 1
        if key == "selected_prompt_key":
            st.session_state[key] = "default" # Default selection



# --- Prompt Templates --- (Keep definitions)
PROMPT_TEMPLATES = {
    "default": {"name": "Technical Focus", "icon": "🔍", "description": "Focuses on technical requirements, action items, and clarifications for URS/SRS/SDS meetings.", "prompt": SUMMARY_DEFAULT_SYSTEM_PROMPT},
    "urs": {"name": "Detailed Requirements", "icon": "📋", "description": "Deep analysis of user requirements with prioritization and dependency tracking.", "prompt": URS_SUMMARY_PROMPT},
    "general": {"name": "General Meeting", "icon": "🗣️", "description": "Summarizes general meetings with focus on decisions, action items, and discussion points.", "prompt": GENERAL_MEETING_PROMPT},
    "overview": {"name": "Executive Overview", "icon": "👔", "description": "Provides a high-level summary suitable for executive stakeholders.", "prompt": OVERVIEW_SUMMARY_PROMPT}
}

# Use st.container(border=True) instead of CSS cards
main_container = st.container(border=False) # Main container for flow, no border needed here.

with main_container:
    # --- Step 1: Upload Transcript ---
    with st.container(border=True): # Use bordered container for grouping
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
                    if file_extension == ".docx": transcript_text = extract_text_from_docx(file_bytes)
                    elif file_extension == ".pdf": transcript_text = extract_text_from_pdf(file_bytes)
                    else: st.error("Unsupported file format.")

                if transcript_text:
                    if transcript_text != st.session_state.get("loaded_transcript_text"):
                        st.session_state.loaded_transcript_text = transcript_text
                        st.session_state.transcript_summary = None
                        st.session_state.exported_summary_path = None
                        st.session_state.current_page = 1
                        # Use Streamlit's success message
                        st.success(f"✅ Successfully loaded and processed: {uploaded_file.name}")
                else:
                    st.session_state.loaded_transcript_text = None
                    st.session_state.transcript_summary = None
                    st.session_state.exported_summary_path = None
            except Exception as e:
                st.error(f"Error processing transcript document: {e}")
                st.session_state.loaded_transcript_text = None
                st.session_state.transcript_summary = None
                st.session_state.exported_summary_path = None

        if st.session_state.get("loaded_transcript_text"):
            with st.expander("Preview Transcript", expanded=False):
                # Simple text display for preview
                st.text(st.session_state.loaded_transcript_text[:1000] + "..." if len(st.session_state.loaded_transcript_text) > 1000 else st.session_state.loaded_transcript_text)

    st.write("") # Add some vertical space

    # --- Step 2: Configure Summary Generation ---
    with st.container(border=True):
        st.subheader("2️⃣ Configure Summary")
        selected_model = st.selectbox(
            "Select AI Model:",
            AVAILABLE_MODELS,
            index=AVAILABLE_MODELS.index("gemini-1.5-pro-latest") if "gemini-1.5-pro-latest" in AVAILABLE_MODELS else 0,
            format_func=lambda x: x.replace("-", " ").title(),
            help="Choose the AI model for generating the summary."
        )
        st.divider() # Use Streamlit divider

        prompt_options = list(PROMPT_TEMPLATES.keys())
        st.session_state.selected_prompt_key = st.radio(
            "Select Summary Template:",
            prompt_options,
            format_func=lambda x: f"{PROMPT_TEMPLATES[x]['icon']} {PROMPT_TEMPLATES[x]['name']}",
            key="summary_template_radio",
            horizontal=True,
            index=prompt_options.index(st.session_state.get("selected_prompt_key", "default"))
        )

        # Use Streamlit's info message
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
            # st.markdown("### Selected Prompt Template")
            # st.markdown(PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["prompt"])

        # custom_prompt_enabled = st.checkbox("Customize prompt instructions")
        # if custom_prompt_enabled:
        #     prompt_to_customize = PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["prompt"]
        #     custom_prompt_key = f"custom_prompt_{st.session_state.selected_prompt_key}"
        #     customized_prompt_text = st.text_area(
        #         "Edit Prompt Instructions:",
        #         value=st.session_state.get(custom_prompt_key, prompt_to_customize),
        #         height=200, key=custom_prompt_key,
        #         help="Modify the base instructions for the AI."
        #     )
        #     st.session_state[custom_prompt_key] = customized_prompt_text
        #     st.session_state.selected_prompt = customized_prompt_text
        # else:
        #     st.session_state.selected_prompt = PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["prompt"]

        additional_focus = st.text_area(
            "Additional Focus Instructions (Optional):",
            placeholder="E.g., 'Focus on budget discussions', 'Highlight security concerns mentioned by John Doe', 'Extract all questions raised'",
            height=100, key="additional_focus_text",
            help="Provide specific keywords or topics for the AI to pay extra attention to."
        )

    st.write("") # Add some vertical space

    # --- Step 3: Generate Summary ---
    # Place button directly, it will likely center in this layout
    generate_button = st.button(
        "🚀 Generate Summary",
        key="generate_summary_button",
        disabled=not st.session_state.get("loaded_transcript_text"),
        help="Upload a transcript document first to enable generation.",
        use_container_width=True # Make button wide for emphasis
    )

    if generate_button and st.session_state.get("loaded_transcript_text"):
        try:
            st.session_state.selected_prompt = PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["prompt"]
            final_prompt = st.session_state.selected_prompt
            if additional_focus: final_prompt += f"\n\n--- Additional Focus Instructions ---\n{additional_focus}"
            with st.spinner(f"⏳ Generating summary using {selected_model}... This may take a moment."):
                summary = summarize_transcription(
                    st.session_state.loaded_transcript_text, model=selected_model, custom_prompt=final_prompt
                )
            st.session_state.transcript_summary = summary
            st.session_state.current_page = 1
            st.session_state.exported_summary_path = None
            st.success("🎉 Summary generated successfully!") # Use built-in success
        except Exception as e:
            st.error(f"❌ Error generating summary: {e}") # Use built-in error
            st.session_state.transcript_summary = None

    st.write("") # Add some vertical space

    # --- Step 4: Display Summary (if generated) ---
    if st.session_state.get("transcript_summary"):
        st.divider()
        st.subheader("📊 Generated Summary")
        with st.container(border=True, height=600): # Bordered container for summary section
            st.write(st.session_state.transcript_summary) # Display the summary text
        st.write("") # Add some vertical space

        # --- Step 5: Export Options ---
        with st.container(border=True):
            st.subheader("💾 Export Summary")
            base_transcript_dir = "transcripts"
            # (Keep folder existence check and listing logic)
            try:
                if not os.path.exists(base_transcript_dir): os.makedirs(base_transcript_dir)
                existing_folders = [d for d in os.listdir(base_transcript_dir) if os.path.isdir(os.path.join(base_transcript_dir, d))]
            except Exception as e:
                st.warning(f"Error accessing transcript folders: {e}")
                existing_folders = []
            existing_folders.sort()
            folder_options = ["Create New Folder"] + existing_folders

            col_folder1, col_folder2 = st.columns([2, 3])
            with col_folder1: selected_folder_option = st.selectbox("Select/Create Folder:", folder_options, key="folder_select_plain")
            output_folder = base_transcript_dir
            with col_folder2:
                if selected_folder_option == "Create New Folder":
                    new_folder_name = st.text_input("New folder name:", key="new_folder_name_plain")
                    if new_folder_name:
                        safe_folder_name = "".join(c for c in new_folder_name if c.isalnum() or c in ('_', '-')).strip()
                        if safe_folder_name: output_folder = os.path.join(base_transcript_dir, safe_folder_name)
                        else: st.warning("Invalid folder name.")
                else: output_folder = os.path.join(base_transcript_dir, selected_folder_option)

            selected_template_name = PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["name"].replace(" ", "_")
            default_filename = f"{selected_template_name}_summary_{datetime.now().strftime('%Y%m%d_%H%M')}"
            export_file_name = st.text_input("File name (no extension):", value=default_filename, key="export_filename_plain")
            safe_export_file_name = "".join(c for c in export_file_name if c.isalnum() or c in ('_', '-')).strip() or "summary_export"

            # Export format buttons using columns
            st.write("") # Space
            col_fmt1, col_fmt2 = st.columns(2)
            export_triggered = False
            export_format = None
            with col_fmt1:
                if st.button("📄 Export as DOCX", key="fmt_docx_plain", use_container_width=True):
                    export_triggered = True; export_format = "DOCX"
            with col_fmt2:
                if st.button("📝 Export as Markdown", key="fmt_md_plain", use_container_width=True):
                    export_triggered = True; export_format = "Markdown"

            # (Keep Export Action logic - using st.success/st.error/st.info)
            if export_triggered and export_format:
                try:
                    if not os.path.exists(output_folder): os.makedirs(output_folder); st.info(f"Created folder: {output_folder}")
                    with st.spinner(f"Exporting summary to {export_format}..."):
                        # ... (Keep docx/md file writing logic) ...
                        if export_format == "DOCX":
                            summary_file_name = f"{safe_export_file_name}.docx"
                            new_var = st.session_state.transcript_summary
                            summary_path = export_summary_to_docx(new_var, output_folder=output_folder, file_name=summary_file_name)
                        else: # Markdown
                            summary_file_name = f"{safe_export_file_name}.md"
                            summary_path = os.path.join(output_folder, summary_file_name)
                            with open(summary_path, "w", encoding="utf-8") as f:
                                f.write(f"---\ntitle: {safe_export_file_name}\ndate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n...") # Keep frontmatter
                                f.write(f"\n---\n\n{st.session_state.transcript_summary}")
                        st.session_state.exported_summary_path = summary_path
                        st.success(f"✅ Summary exported successfully to: `{summary_path}`") # Use built-in success
                except Exception as e:
                    st.error(f"❌ Error exporting summary: {e}") # Use built-in error
                    st.session_state.exported_summary_path = None

            # --- Download Button ---
            if st.session_state.get("exported_summary_path") and os.path.exists(st.session_state.exported_summary_path):
                st.write("") # Space
                file_path = st.session_state.exported_summary_path
                file_name = os.path.basename(file_path)
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if file_path.endswith(".docx") else "text/markdown"
                icon = "📄" if file_path.endswith(".docx") else "📝"
                try:
                    with open(file_path, "rb") as file:
                        # Place download button directly
                        st.download_button(
                            label=f"{icon} Download '{file_name}'",
                            data=file, file_name=file_name, mime=mime_type,
                            key="download_plain",
                            use_container_width=True # Make it wide
                        )
                except Exception as e:
                    st.error(f"Error preparing download: {e}") # Use built-in error

    # --- Placeholders --- (Using st.info)
    elif not st.session_state.get("loaded_transcript_text"):
        st.info("⬆️ Upload a transcript document (DOCX or PDF) to get started.")
    elif st.session_state.get("loaded_transcript_text") and not st.session_state.get("transcript_summary"):
         # Check if button was just clicked (state might not have updated yet)
         # A simple check might be enough here if generate_button is True
         # Or just always show the info if no summary
         st.info("⚙️ Configure the summary options above and click 'Generate Summary'.")


# --- Footer --- (Using st.expander)
st.divider()
with st.expander("💡 Tips for Better Summaries"):
    st.markdown("""
    *   **Choose the right template:** Match the template (Technical, Requirements, General, Overview) to your meeting's primary purpose.
    *   **Use 'Additional Focus':** Guide the AI by listing specific names, projects, keywords, or types of information (e.g., 'all decisions made', 'budget concerns', 'tasks assigned to Sarah').
    *   **Customize Prompt (Advanced):** If the standard templates aren't perfect, tweak the instructions directly for fine-grained control.
    *   **PDF Quality Matters:** Ensure your PDF contains selectable text, not just images of text, for reliable extraction.
    *   **Review & Refine:** AI summaries are a great starting point. Always review for accuracy and completeness, especially for critical information.
    """)