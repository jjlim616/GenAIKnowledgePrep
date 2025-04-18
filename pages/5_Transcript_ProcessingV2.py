# pages/5_Transcript_ProcessingV2.py
import streamlit as st
import os
import uuid
import tempfile
import io
from datetime import datetime
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

# Page configuration and layout
st.set_page_config(
    page_title="Transcript Processing",
    page_icon="📄",
    layout="wide", # Keep wide layout for better use of space in single column
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner, more modern look (minor adjustments if needed)
st.markdown("""
    <style>
    /* Main page styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        /* Max width can be wider for single column if desired, or keep as is */
        max-width: 900px;
        margin: 0 auto; /* Center the content */
    }

    /* Typography */
    h1 {
        font-weight: 700;
        margin-bottom: 1.5rem;
        color: #1E3A8A; /* Dark Blue */
        text-align: center; /* Center main title */
    }

    h2, h3 {
        font-weight: 600;
        margin-top: 1.5rem; /* Reduced top margin for headings */
        margin-bottom: 1rem;
        color: #2563EB; /* Medium Blue */
    }
    .subheader {
        font-weight: 400; /* Lighter weight for subheader */
        text-align: center;
        color: #4B5563; /* Gray */
        margin-bottom: 2rem;
    }

    /* Card-like containers */
    .card {
        background-color: #FFFFFF;
        border-radius: 12px; /* Slightly more rounded */
        padding: 1.5rem 2rem; /* Adjust padding */
        box-shadow: 0 2px 5px rgba(0,0,0,0.08); /* Softer shadow */
        margin-bottom: 2rem; /* Increased spacing between cards */
        border: 1px solid #E5E7EB; /* Light gray border */
    }

    /* Pagination styles */
    .pagination {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 1.5rem; /* Increased margin */
        margin-bottom: 1rem;
    }

    .pagination .page-btn {
        margin: 0 0.3rem;
        min-width: 2.2rem; /* Slightly larger */
        text-align: center;
    }

    .pagination .page-info {
        margin: 0 0.8rem; /* Increased spacing */
        font-size: 1rem; /* Slightly larger */
        color: #4B5563;
    }

    /* Buttons styling */
    .stButton > button {
        background-color: #2563EB; /* Medium Blue */
        color: white;
        border: none;
        padding: 0.6rem 1.2rem; /* Slightly larger padding */
        border-radius: 6px; /* More rounded */
        font-weight: 500;
        transition: all 0.2s;
        width: auto; /* Allow button to size naturally */
        display: inline-block; /* Needed for centering if wrapped in div */
    }

    .stButton > button:hover {
        background-color: #1E40AF; /* Darker Blue */
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Page navigation buttons */
    .nav-btn > button {
        background-color: #E0E7FF; /* Lighter blue */
        color: #374151; /* Darker text */
        font-size: 0.9rem;
        padding: 0.4rem 0.8rem;
        border: 1px solid #C7D2FE; /* Subtle border */
    }

    .nav-btn > button:hover {
        background-color: #C7D2FE;
    }

    /* Current page button */
    .current-page > button {
        background-color: #3B82F6; /* Brighter blue */
        color: white;
        font-weight: 600;
        border: 1px solid #2563EB;
    }

    /* Download button */
    .download-btn > button {
        background-color: #10B981; /* Green */
        color: white;
    }

    .download-btn > button:hover {
        background-color: #059669; /* Darker Green */
    }

    /* File uploader */
    .uploadedFile {
        border: 2px dashed #CBD5E1; /* Thicker dash */
        border-radius: 8px;
        padding: 1.5rem;
        background-color: #F8FAFC; /* Very light gray */
    }

    /* Radio buttons */
    .stRadio > label {
        font-weight: 500; /* Make radio label slightly bolder */
        margin-bottom: 0.8rem;
    }
    .stRadio > div {
        margin-bottom: 0.5rem;
    }

    /* Info blocks */
    .info-block {
        background-color: #EFF6FF; /* Lighter blue */
        border-left: 4px solid #60A5FA; /* Softer blue border */
        padding: 1rem 1.5rem;
        border-radius: 6px;
        margin-top: 0.5rem; /* Add some space above */
        margin-bottom: 1rem;
        font-size: 0.95rem;
    }

    /* Success message */
    .success-msg {
        background-color: #ECFDF5; /* Lighter green */
        border-left: 4px solid #34D399; /* Softer green border */
        padding: 1rem 1.5rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-size: 0.95rem;
    }

    /* Center align elements */
    .center-button {
        text-align: center;
        margin-top: 1rem; /* Add space above centered button */
    }

    /* Export Buttons Container */
    .export-buttons {
        display: flex;
        gap: 1rem; /* Space between buttons */
        margin-top: 1rem; /* Space above buttons */
        justify-content: center; /* Center buttons */
    }
    </style>
""", unsafe_allow_html=True)

# Header with icon and title (adjusted for centering)
st.markdown('<div style="text-align: center; margin-bottom: 0.5rem;">'
            '<span style="font-size: 2.5rem;">📝</span>'
            '</div>', unsafe_allow_html=True)
st.markdown('<h1>Transcript Processing & Summaries</h1>', unsafe_allow_html=True)
st.markdown('<p class="subheader">Transform your meeting transcripts into concise, actionable summaries.</p>',
            unsafe_allow_html=True)

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
for key in ["loaded_transcript_text", "selected_prompt_key", "selected_prompt", "summary", "exported_summary_path", "current_page"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "current_page" else 1
        if key == "selected_prompt_key":
            st.session_state[key] = "default" # Default selection


# --- Helper Functions ---

def paginate_text(text, page_size=2000):
    """Split text into pages of approximately page_size characters."""
    if not text: return [""] # Handle empty text
    paragraphs = text.split('\n\n')
    pages = []
    current_page_content = ""
    for paragraph in paragraphs:
        if len(current_page_content) + len(paragraph) < page_size:
            current_page_content += paragraph + "\n\n"
        else:
            if current_page_content:
                pages.append(current_page_content.strip())
            # Handle case where a single paragraph exceeds page size
            if len(paragraph) >= page_size:
                 # Simple split for oversized paragraphs (can be improved)
                 parts = [paragraph[i:i+page_size] for i in range(0, len(paragraph), page_size)]
                 pages.extend(parts)
                 current_page_content = "" # Reset after handling long paragraph
            else:
                current_page_content = paragraph + "\n\n"

    if current_page_content:
        pages.append(current_page_content.strip())
    # Ensure there's at least one page if text exists
    if not pages and text:
        pages.append(text)
    return pages if pages else [""]


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

# --- Prompt Templates ---
PROMPT_TEMPLATES = {
    "default": {
        "name": "Technical Focus",
        "icon": "🔍",
        "description": "Focuses on technical requirements, action items, and clarifications for URS/SRS/SDS meetings.",
        "prompt": SUMMARY_DEFAULT_SYSTEM_PROMPT
    },
    "urs": {
        "name": "Detailed Requirements",
        "icon": "📋",
        "description": "Deep analysis of user requirements with prioritization and dependency tracking.",
        "prompt": URS_SUMMARY_PROMPT
    },
    "general": {
        "name": "General Meeting",
        "icon": "🗣️",
        "description": "Summarizes general meetings with focus on decisions, action items, and discussion points.",
        "prompt": GENERAL_MEETING_PROMPT
    },
    "overview": {
        "name": "Executive Overview",
        "icon": "👔",
        "description": "Provides a high-level summary suitable for executive stakeholders.",
        "prompt": OVERVIEW_SUMMARY_PROMPT
    }
}

# --- Step 1: Upload Transcript ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 1️⃣ Upload Transcript Document")

uploaded_file = st.file_uploader(
    "Upload a transcript (DOCX or PDF):",
    type=["docx", "pdf"],
    key="doc_transcript_uploader",
    label_visibility="collapsed", # Hide default label as we have a heading
    help="Maximum file size: 200MB"
)

if uploaded_file:
    # Store file info for potential later use if needed
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
                st.error("Unsupported file format. Please upload a DOCX or PDF file.")

        if transcript_text:
            # Only update if text extraction was successful and different from current
            if transcript_text != st.session_state.get("loaded_transcript_text"):
                st.session_state.loaded_transcript_text = transcript_text
                st.session_state.summary = None # Reset summary if new transcript loaded
                st.session_state.exported_summary_path = None # Reset export path
                st.session_state.current_page = 1 # Reset page
                st.markdown(f'<div class="success-msg">✅ Successfully loaded and processed: {uploaded_file.name}</div>', unsafe_allow_html=True)
        else:
            # Clear loaded text if extraction failed
            st.session_state.loaded_transcript_text = None
            st.session_state.summary = None
            st.session_state.exported_summary_path = None

    except Exception as e:
        st.error(f"Error processing transcript document: {e}")
        st.session_state.loaded_transcript_text = None
        st.session_state.summary = None
        st.session_state.exported_summary_path = None

# Display preview only if text is loaded
if st.session_state.get("loaded_transcript_text"):
    with st.expander("Preview Transcript", expanded=False):
        st.markdown('<div style="max-height: 250px; overflow-y: auto; font-family: monospace; font-size: 0.85rem; padding: 10px; background-color: #F8FAFC; border-radius: 4px; border: 1px solid #E5E7EB;">', unsafe_allow_html=True)
        preview_lines = st.session_state.loaded_transcript_text.split('\n')[:30]  # Show more lines
        preview_text = "\n".join(preview_lines)
        if len(st.session_state.loaded_transcript_text.split('\n')) > 30:
            preview_text += "\n\n[...]"
        st.text(preview_text)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) # End Upload Card


# --- Step 2: Configure Summary Generation ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 2️⃣ Configure Summary")

# Model Selection
selected_model = st.selectbox(
    "Select AI Model:",
    AVAILABLE_MODELS,
    index=AVAILABLE_MODELS.index("gemini-1.5-pro-latest") if "gemini-1.5-pro-latest" in AVAILABLE_MODELS else 0, # Default to 1.5 Pro
    format_func=lambda x: x.replace("-", " ").title(),
    help="Choose the AI model for generating the summary."
)

st.markdown("---") # Visual separator within the card

# Summary Format Selection
prompt_options = list(PROMPT_TEMPLATES.keys())
st.session_state.selected_prompt_key = st.radio(
    "Select Summary Template:",
    prompt_options,
    format_func=lambda x: f"{PROMPT_TEMPLATES[x]['icon']} {PROMPT_TEMPLATES[x]['name']}",
    key="summary_template_radio", # Ensure unique key
    horizontal=True, # Display options side-by-side if space allows
    index=prompt_options.index(st.session_state.get("selected_prompt_key", "default")) # Maintain selection
)

# Display prompt description
st.markdown(f'<div class="info-block">{PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["description"]}</div>', unsafe_allow_html=True)

# Option to customize the prompt
custom_prompt_enabled = st.checkbox("Customize prompt instructions")
if custom_prompt_enabled:
    prompt_to_customize = PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["prompt"]
    # Use a unique key for the text_area based on the selected prompt to avoid state issues
    custom_prompt_key = f"custom_prompt_{st.session_state.selected_prompt_key}"
    customized_prompt_text = st.text_area(
        "Edit Prompt Instructions:",
        value=st.session_state.get(custom_prompt_key, prompt_to_customize), # Load saved custom prompt if exists
        height=200,
        key=custom_prompt_key,
        help="Modify the base instructions for the AI."
    )
    st.session_state[custom_prompt_key] = customized_prompt_text # Save changes
    st.session_state.selected_prompt = customized_prompt_text
else:
    # Ensure the correct default prompt is set when checkbox is unchecked
    st.session_state.selected_prompt = PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["prompt"]
    # Clear any saved custom text for this template to avoid confusion
    # st.session_state.pop(f"custom_prompt_{st.session_state.selected_prompt_key}", None) # Optional: Clear saved custom text


# Additional focus instructions
additional_focus = st.text_area(
    "Additional Focus Instructions (Optional):",
    placeholder="E.g., 'Focus on budget discussions', 'Highlight security concerns mentioned by John Doe', 'Extract all questions raised'",
    height=100,
    key="additional_focus_text",
    help="Provide specific keywords or topics for the AI to pay extra attention to."
)

st.markdown('</div>', unsafe_allow_html=True) # End Configure Card


# --- Step 3: Generate Summary ---
st.markdown('<div class="center-button">', unsafe_allow_html=True) # Centering the button
generate_button = st.button(
    "🚀 Generate Summary",
    key="generate_summary_button",
    disabled=not st.session_state.get("loaded_transcript_text"),
    help="Upload a transcript document first to enable generation.",
    use_container_width=False # Don't make button full width
)
st.markdown('</div>', unsafe_allow_html=True)

if generate_button and st.session_state.get("loaded_transcript_text"):
    try:
        # Combine base prompt (customized or default) with additional focus
        final_prompt = st.session_state.selected_prompt
        if additional_focus:
            final_prompt += f"\n\n--- Additional Focus Instructions ---\n{additional_focus}"

        with st.spinner(f"⏳ Generating summary using {selected_model}... This may take a moment."):
            summary = summarize_transcription(
                st.session_state.loaded_transcript_text,
                model=selected_model,
                custom_prompt=final_prompt
            )
        st.session_state.summary = summary
        st.session_state.current_page = 1  # Reset to first page
        st.session_state.exported_summary_path = None # Reset export path
        st.success("🎉 Summary generated successfully!")
        # st.rerun() # Rerun might not be needed if elements appear conditionally below
    except Exception as e:
        st.error(f"❌ Error generating summary: {e}")
        st.session_state.summary = None # Clear summary on error


# --- Step 4: Display Summary (if generated) ---
if st.session_state.get("summary"):
    st.divider() # Visual separator before results
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📊 Generated Summary")

    # Paginate the summary
    summary_pages = paginate_text(st.session_state.summary)
    total_pages = len(summary_pages)

    # Ensure current page is valid
    if st.session_state.current_page < 1: st.session_state.current_page = 1
    if st.session_state.current_page > total_pages: st.session_state.current_page = total_pages

    # # Display current page content
    # st.markdown(f'<div style="background-color: #F8FAFC; padding: 15px; border-radius: 6px; border: 1px solid #E5E7EB; min-height: 200px; max-height: 400px; overflow-y: auto;">', unsafe_allow_html=True)
    with st.container(height = 700):
        st.markdown(summary_pages[st.session_state.current_page - 1])
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Pagination Controls ---
    if total_pages > 1:
        # Use a container to potentially help with centering or styling later if needed
        pagination_container = st.container()
        with pagination_container:
            col_prev, col_info, col_next = st.columns([
                2, # Adjust ratios: give buttons slightly more space relative to center
                3,
                2
            ])

            with col_prev:
                if st.session_state.current_page > 1:
                    # Use markdown to wrap the button and align it right within the column
                    st.markdown('<div style="text-align: right; width: 100%;">', unsafe_allow_html=True)
                    if st.button("← Prev", key="prev_page", help="Go to previous page"):
                        st.session_state.current_page -= 1
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.write("") # Placeholder to maintain structure if button not shown

            with col_info:
                # Ensure vertical alignment using line-height matching button height approximately
                # Or use padding. Adjust line-height/padding as needed based on button style.
                st.markdown(
                    f'<p class="page-info" style="text-align: center; margin: 0; line-height: 2.5; white-space: nowrap;">Page {st.session_state.current_page} of {total_pages}</p>',
                    unsafe_allow_html=True
                )

            with col_next:
                if st.session_state.current_page < total_pages:
                    # Use markdown to wrap the button and align it left (default, but explicit)
                    st.markdown('<div style="text-align: left; width: 100%;">', unsafe_allow_html=True)
                    if st.button("Next →", key="next_page", help="Go to next page"):
                        st.session_state.current_page += 1
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.write("") # Placeholder

        # Remove the outer pagination div if the container handles structure well enough
        # st.markdown('<div class="pagination">', unsafe_allow_html=True)
        # ... (column code as above) ...
        # st.markdown('</div>', unsafe_allow_html=True)

        # --- Quick Page Navigation (Enhanced) ---
        if total_pages > 5: # Show quick nav only if more than 5 pages
            st.markdown('<div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 5px; margin-top: 10px;">', unsafe_allow_html=True)

            page_numbers_to_show = set()
            current_page = st.session_state.current_page

            # Always show first and last
            page_numbers_to_show.add(1)
            page_numbers_to_show.add(total_pages)

            # Show pages around current
            page_numbers_to_show.add(max(1, current_page - 1))
            page_numbers_to_show.add(current_page)
            page_numbers_to_show.add(min(total_pages, current_page + 1))

            # Show pages around the middle (optional, adjust as needed)
            # mid_point = total_pages // 2
            # page_numbers_to_show.add(max(1, mid_point -1))
            # page_numbers_to_show.add(mid_point)
            # page_numbers_to_show.add(min(total_pages, mid_point + 1))

            sorted_pages = sorted(list(page_numbers_to_show))

            # Create buttons with ellipsis logic
            last_page_shown = 0
            buttons_html = ""
            for page in sorted_pages:
                if page > last_page_shown + 1:
                    # Add ellipsis
                    buttons_html += '<span style="margin: 0 5px; align-self: center;">...</span>'

                button_class = "current-page" if page == current_page else ""
                # Use st.button within the loop for interactivity
                # We need to structure this differently for Streamlit buttons
                # Let's use columns instead of pure HTML for buttons

                last_page_shown = page

            # Create buttons using columns (simpler Streamlit approach)
            nav_cols = st.columns(len(sorted_pages))
            for i, page in enumerate(sorted_pages):
                 with nav_cols[i]:
                      is_current = (page == current_page)
                      button_type = "primary" if is_current else "secondary"
                      if st.button(f"{page}", key=f"page_{page}", help=f"Go to page {page}", type=button_type, use_container_width=True):
                           if not is_current:
                               st.session_state.current_page = page
                               st.rerun()


            st.markdown('</div>', unsafe_allow_html=True) # End quick nav div

    st.markdown('</div>', unsafe_allow_html=True) # End Summary Card

    # --- Step 5: Export Options (if summary exists) ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 💾 Export Summary")

    base_transcript_dir = "transcripts"
    if not os.path.exists(base_transcript_dir):
        try:
            os.makedirs(base_transcript_dir)
        except OSError as e:
            st.warning(f"Could not create base directory '{base_transcript_dir}': {e}. Exporting may fail.")

    try:
        existing_folders = [d for d in os.listdir(base_transcript_dir) if os.path.isdir(os.path.join(base_transcript_dir, d))]
    except FileNotFoundError:
         st.warning(f"Base directory '{base_transcript_dir}' not found. Please create it manually or check permissions.")
         existing_folders = []
    except Exception as e:
         st.warning(f"Error listing folders in '{base_transcript_dir}': {e}")
         existing_folders = []

    existing_folders.sort() # Sort alphabetically
    folder_options = ["Create New Folder"] + existing_folders

    # Folder selection layout
    col_folder1, col_folder2 = st.columns([2, 3]) # Adjust ratio as needed
    with col_folder1:
        selected_folder_option = st.selectbox("Select or Create Folder:", folder_options, key="folder_select")

    output_folder = base_transcript_dir # Default to base if creation fails or no input
    new_folder_name = ""
    with col_folder2:
        if selected_folder_option == "Create New Folder":
            new_folder_name = st.text_input("New folder name:", value="", placeholder="e.g., Project_Alpha_Summaries", key="new_folder_name")
            if new_folder_name:
                # Basic sanitization (replace spaces, remove invalid chars - adjust as needed)
                safe_folder_name = "".join(c for c in new_folder_name if c.isalnum() or c in ('_', '-')).strip()
                if safe_folder_name:
                    output_folder = os.path.join(base_transcript_dir, safe_folder_name)
                else:
                    st.warning("Invalid folder name provided. Using base directory.")
                    output_folder = base_transcript_dir
            # else: output_folder remains base_transcript_dir
        else:
            output_folder = os.path.join(base_transcript_dir, selected_folder_option)

    # Filename input
    selected_template_name = PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["name"].replace(" ", "_")
    default_filename = f"{selected_template_name}_summary_{datetime.now().strftime('%Y%m%d_%H%M')}"
    export_file_name = st.text_input("Enter file name (without extension):", value=default_filename, key="export_filename")
    safe_export_file_name = "".join(c for c in export_file_name if c.isalnum() or c in ('_', '-')).strip() or "summary_export"


    # Export format buttons
    st.markdown("<div class='export-buttons'>", unsafe_allow_html=True)
    col_fmt1, col_fmt2 = st.columns(2)
    export_triggered = False
    export_format = None

    with col_fmt1:
        if st.button("📄 Export as DOCX", key="fmt_docx", use_container_width=True):
             export_triggered = True
             export_format = "DOCX"
    with col_fmt2:
        if st.button("📝 Export as Markdown", key="fmt_md", use_container_width=True):
             export_triggered = True
             export_format = "Markdown"
    st.markdown("</div>", unsafe_allow_html=True)


    # Handle Export Action
    if export_triggered and export_format:
        try:
            # Ensure output folder exists (especially if creating new)
            if not os.path.exists(output_folder):
                try:
                    os.makedirs(output_folder)
                    st.info(f"Created folder: {output_folder}")
                except OSError as e:
                    st.error(f"Could not create folder '{output_folder}': {e}. Cannot export.")
                    export_triggered = False # Prevent further processing

            if export_triggered: # Check again if folder creation succeeded
                with st.spinner(f"Exporting summary to {export_format}..."):
                    if export_format == "DOCX":
                        summary_file_name = f"{safe_export_file_name}.docx"
                        summary_path = export_summary_to_docx(
                            st.session_state.summary,
                            output_folder=output_folder,
                            file_name=summary_file_name
                        )
                    else:  # Markdown
                        summary_file_name = f"{safe_export_file_name}.md"
                        summary_path = os.path.join(output_folder, summary_file_name)

                        # Create markdown file with frontmatter
                        with open(summary_path, "w", encoding="utf-8") as f:
                            f.write(f"""---
title: {safe_export_file_name}
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
template: {PROMPT_TEMPLATES[st.session_state.selected_prompt_key]["name"]}
model: {selected_model}
source_file: {st.session_state.get('uploaded_filename', 'N/A')}
---

{st.session_state.summary}
""")

                    st.session_state.exported_summary_path = summary_path
                    st.success(f"✅ Summary exported successfully to: `{summary_path}`")
                    # Trigger rerun ONLY if download button state needs update based on new path
                    # st.rerun()
        except Exception as e:
            st.error(f"❌ Error exporting summary: {e}")
            st.session_state.exported_summary_path = None


    # --- Download Button (if export path exists) ---
    if st.session_state.get("exported_summary_path") and os.path.exists(st.session_state.exported_summary_path):
        file_path = st.session_state.exported_summary_path
        file_name = os.path.basename(file_path)
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if file_path.endswith(".docx") else "text/markdown"
        icon = "📄" if file_path.endswith(".docx") else "📝"

        try:
            with open(file_path, "rb") as file:
                st.markdown('<div class="center-button download-btn" style="margin-top: 1.5rem;">', unsafe_allow_html=True)
                st.download_button(
                    label=f"{icon} Download '{file_name}'",
                    data=file,
                    file_name=file_name,
                    mime=mime_type,
                    key="download_exported_summary"
                )
                st.markdown('</div>', unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning(f"Could not find the exported file at '{file_path}' for download.")
            st.session_state.exported_summary_path = None # Clear invalid path
        except Exception as e:
            st.error(f"Error preparing download button: {e}")


    st.markdown('</div>', unsafe_allow_html=True) # End Export Card

# --- Placeholder if no summary generated yet ---
elif not st.session_state.get("loaded_transcript_text"):
    st.info("⬆️ Upload a transcript document (DOCX or PDF) to get started.")
elif st.session_state.get("loaded_transcript_text") and not st.session_state.get("summary"):
     # Only show this if generate hasn't been clicked or failed
     if not generate_button: # Check if button was clicked in this run
        st.info("⚙️ Configure the summary options above and click 'Generate Summary'.")


# --- Footer ---
st.divider()
with st.expander("💡 Tips for Better Summaries"):
    st.markdown("""
    *   **Choose the right template:** Match the template (Technical, Requirements, General, Overview) to your meeting's primary purpose.
    *   **Use 'Additional Focus':** Guide the AI by listing specific names, projects, keywords, or types of information (e.g., 'all decisions made', 'budget concerns', 'tasks assigned to Sarah').
    *   **Customize Prompt (Advanced):** If the standard templates aren't perfect, tweak the instructions directly for fine-grained control.
    *   **PDF Quality Matters:** Ensure your PDF contains selectable text, not just images of text, for reliable extraction.
    *   **Review & Refine:** AI summaries are a great starting point. Always review for accuracy and completeness, especially for critical information.
    """)