# pages/3_Transcript_Processing.py
import streamlit as st
import os
import uuid
import tempfile
import io
from datetime import datetime
import pypandoc
import docx2txt
import fitz  # PyMuPDF
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
from src.audio_processor import (
    summarize_transcription,
    export_summary_to_docx
)

st.title("Transcript Processing & Custom Summaries")
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-size: 16px;
        cursor: pointer;
    }
    div.stButton > button:hover {
        background-color: #45a049;
    }
    div.stDownloadButton > button {
        background-color: #008CBA;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-size: 16px;
        cursor: pointer;
    }
    div.stDownloadButton > button:hover {
        background-color: #007bb5;
    }
    </style>
""", unsafe_allow_html=True)
st.write("Upload an existing transcript document (DOCX or PDF) and generate customized summaries using different prompt templates.")

# Define available Gemini models
AVAILABLE_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-pro-exp-03-25",
    "gemini-1.5-pro-latest"
]

# # Session state initialization
# if "session_id" not in st.session_state:
#     st.session_state.session_id = uuid.uuid4().hex

# Initialize session and check for expiry
initialize_session()
if not check_session_expiry(max_inactivity_days=1):
    st.warning("Session has expired due to inactivity. Starting a new session.")
    initialize_session()
update_activity_timestamp()

for key in ["loaded_transcript_text", "selected_prompt", "summary", "exported_summary_path"]:
    if key not in st.session_state:
        st.session_state[key] = None

def extract_text_from_docx(file_bytes):
    """Extract text from a DOCX file."""
    try:
        text = docx2txt.process(io.BytesIO(file_bytes))
        return text
    except Exception as e:
        st.error(f"Error extracting text from DOCX: {e}")
        return None

def extract_text_from_pdf(file_bytes):
    """Extract text from a PDF file."""
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return None

# Define prompt templates with descriptions
PROMPT_TEMPLATES = {
    "default": {
        "name": "Default (URS/SRS/SDS Technical Focus)",
        "description": "Focuses on technical requirements, action items, and clarifications for URS/SRS/SDS meetings.",
        "prompt": SUMMARY_DEFAULT_SYSTEM_PROMPT
    },
    "urs": {
        "name": "URS Detailed Requirements",
        "description": "Deep analysis of user requirements with prioritization and dependency tracking.",
        "prompt": URS_SUMMARY_PROMPT
    },
    "general": {
        "name": "General Meeting",
        "description": "Summarizes general meetings with focus on decisions, action items, and discussion points.",
        "prompt": GENERAL_MEETING_PROMPT
    },
    "overview": {
        "name": "Executive Overview",
        "description": "Provides a high-level summary suitable for executive stakeholders.",
        "prompt": OVERVIEW_SUMMARY_PROMPT
    }
}

# File uploader for DOCX/PDF transcript file
uploaded_file = st.file_uploader("Upload a transcript document", type=["docx", "pdf"], key="doc_transcript_uploader")

if uploaded_file:
    try:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        file_bytes = uploaded_file.getvalue()
        
        if file_extension == ".docx":
            transcript_text = extract_text_from_docx(file_bytes)
        elif file_extension == ".pdf":
            transcript_text = extract_text_from_pdf(file_bytes)
        else:
            st.error("Unsupported file format. Please upload a DOCX or PDF file.")
            transcript_text = None
            
        if transcript_text:
            st.session_state.loaded_transcript_text = transcript_text
            st.success(f"Transcript content extracted successfully from {uploaded_file.name}.")
            
            # Display transcript preview
            with st.expander("Preview Loaded Transcript"):
                preview_lines = transcript_text.split('\n')[:20]  # First 20 lines
                for line in preview_lines:
                    st.text(line)
                
                if len(transcript_text.split('\n')) > 20:
                    st.markdown(f"*...and more content*")
    except Exception as e:
        st.error(f"Error processing transcript document: {e}")

# Model selection
selected_model = st.selectbox("Select LLM Model", AVAILABLE_MODELS, index=0)

# Prompt template selection
st.subheader("Select Summary Format")
prompt_options = list(PROMPT_TEMPLATES.keys())
selected_prompt_key = st.radio(
    "Choose a prompt template:",
    prompt_options,
    format_func=lambda x: PROMPT_TEMPLATES[x]["name"]
)

# Display prompt description
st.info(PROMPT_TEMPLATES[selected_prompt_key]["description"])

# Option to customize the prompt
custom_prompt = st.checkbox("Customize prompt")
if custom_prompt:
    prompt_to_customize = PROMPT_TEMPLATES[selected_prompt_key]["prompt"]
    customized_prompt = st.text_area("Edit Prompt", value=prompt_to_customize, height=300)
    st.session_state.selected_prompt = customized_prompt
else:
    st.session_state.selected_prompt = PROMPT_TEMPLATES[selected_prompt_key]["prompt"]

# Additional focus instructions
additional_focus = st.text_area(
    "Additional Focus Instructions (Optional)", 
    placeholder="E.g., 'Pay special attention to budget discussions' or 'Highlight any security concerns mentioned'"
)

# Generate Summary button
if st.button("Generate Summary") and st.session_state.loaded_transcript_text:
    try:
        full_prompt = st.session_state.selected_prompt
        if additional_focus:
            full_prompt += f"\n\nAdditional Focus Instructions: {additional_focus}"
            
        with st.spinner("Generating summary..."):
            summary = summarize_transcription(
                st.session_state.loaded_transcript_text, 
                model=selected_model,
                custom_prompt=full_prompt
            )
        st.session_state.summary = summary
        st.success("Summary generated successfully!")
    except Exception as e:
        st.error(f"Error generating summary: {e}")

# Display Summary
if st.session_state.summary:
    st.subheader("Generated Summary")
    with st.container(height=500):
        st.markdown(st.session_state.summary)

# Export options
if st.session_state.summary:
    st.subheader("Export Summary")
    
    base_transcript_dir = "transcripts"
    if not os.path.exists(base_transcript_dir):
        os.makedirs(base_transcript_dir)
    existing_folders = [d for d in os.listdir(base_transcript_dir) if os.path.isdir(os.path.join(base_transcript_dir, d))]
    existing_folders.insert(0, "Create New Folder")

    selected_folder_option = st.selectbox("Select or Create Folder", existing_folders)

    if selected_folder_option == "Create New Folder":
        new_folder_name = st.text_input("Enter new folder name (e.g., Project_X)", value="")
        output_folder = os.path.join(base_transcript_dir, new_folder_name) if new_folder_name else base_transcript_dir
    else:
        output_folder = os.path.join(base_transcript_dir, selected_folder_option)

    # Default filename based on template and date
    default_filename = f"{selected_prompt_key}_summary_{datetime.now().strftime('%Y%m%d')}"
    export_file_name = st.text_input("Enter file name (without extension)", value=default_filename)

    # Export format options
    export_format = st.radio("Export Format", ["DOCX", "Markdown"], horizontal=True)

    if st.button(f"Export Summary as {export_format}"):
        try:
            with st.spinner(f"Exporting summary to {export_format}..."):
                if export_format == "DOCX":
                    summary_file_name = f"{export_file_name}.docx"
                    summary_path = export_summary_to_docx(
                        st.session_state.summary,
                        output_folder=output_folder,
                        file_name=summary_file_name
                    )
                else:  # Markdown
                    summary_file_name = f"{export_file_name}.md"
                    os.makedirs(output_folder, exist_ok=True)
                    summary_path = os.path.join(output_folder, summary_file_name)
                    
                    # Create markdown file with frontmatter
                    with open(summary_path, "w", encoding="utf-8") as f:
                        f.write(f"""---
title: {export_file_name}
date: {datetime.now().strftime('%Y-%m-%d')}
template: {PROMPT_TEMPLATES[selected_prompt_key]["name"]}
---

{st.session_state.summary}
""")
                
                st.session_state.exported_summary_path = summary_path
                st.success(f"🎉 Summary exported to server at {output_folder}! Use the button below to download to your device.")
        except Exception as e:
            st.error(f"Error exporting summary: {e}")

    # Download button
    if "exported_summary_path" in st.session_state and st.session_state.exported_summary_path is not None:
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if export_format == "DOCX" else "text/markdown"
        icon = "📝" if export_format == "DOCX" else "📄"
        
        with open(st.session_state.exported_summary_path, "rb") as file:
            st.download_button(
                label=f"{icon} Download Summary {export_format}",
                data=file,
                file_name=os.path.basename(st.session_state.exported_summary_path),
                mime=mime_type
            )
        st.caption("💾 This button downloads the file from the server to your device.")

