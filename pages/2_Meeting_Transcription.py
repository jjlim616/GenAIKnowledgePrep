# pages/2_Meeting_Transcription.py
# Standard libraries
import os
import shutil
import tempfile

# Third-party libraries
import streamlit as st

# Local application imports
from src.utils import (
    initialize_session,
    update_activity_timestamp,
    check_session_expiry,
    clear_session,
)
from src.prompts import TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT
from src.audio_processor import (
    transcribe_audio_with_diarization,
    delete_uploaded_file,
    parse_timestamp_to_seconds,
)
from src.text_processor import (
    summarize_transcription,
    export_summary_to_docx,
    export_transcription_to_docx,
)

# Initialize session and check for expiry
initialize_session()
if not check_session_expiry(max_inactivity_days=1):
    st.warning("Session has expired due to inactivity. Starting a new session.")
    initialize_session()
update_activity_timestamp()

# Page title and description
st.title("Meeting Transcription and Summarization")
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
    /* Highlight active step */
    .active-step {
        background-color: #f0f8ff;
        border: 2px solid #4CAF50 !important;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)
st.write("Upload an MP3, M4A, or WAV file of a recorded meeting to transcribe it with speaker diarization and generate a summary.")

# Define available Gemini models
AVAILABLE_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-pro-exp-03-25",
    "gemini-1.5-pro-latest"
]

# Session state initialization for other keys
for key in ["transcription_json", "audio_bytes", "uploaded_audio", "summary", "selected_time", "transcription_done", "exported_transcript_path", "exported_summary_path"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "selected_time" else 0

# Determine the current step for highlighting
current_step = 1
if st.session_state.uploaded_audio:
    current_step = 2
if st.session_state.transcription_done:
    current_step = 3
if st.session_state.summary:
    current_step = 4
if st.session_state.exported_transcript_path:
    current_step = 5

# Display progress tracker
st.markdown(f"**Progress: Step {current_step} of 5**")

# Step 1: Upload Audio File
with st.container(border=True) as step1_container:
    st.subheader("Step 1: Upload Audio File")
    uploaded_file = st.file_uploader("Upload an MP3, M4A, or WAV file", type=["mp3", "m4a", "wav"], key="uploader_tab3")
    if not uploaded_file:
        st.info("Upload a file to proceed to transcription.", icon="ℹ️")

if uploaded_file and not st.session_state.uploaded_audio:
    # Store the uploaded file in session state to persist across reruns
    audio_bytes = uploaded_file.getvalue()
    st.session_state.update({
        "audio_bytes": audio_bytes,
        "uploaded_audio": uploaded_file  # Store the uploaded file object
    })

# Highlight Step 1 if active
if current_step == 1:
    st.markdown("""
        <script>
        document.querySelectorAll('[data-testid="stVerticalBlock"] > div')[0].classList.add('active-step');
        </script>
    """, unsafe_allow_html=True)

# Step 2: Transcription Settings
with st.container(border=True) as step2_container:
    st.subheader("Step 2: Transcription Settings")
    if st.session_state.uploaded_audio:
        full_prompt = TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT
        selected_model = st.selectbox("Select LLM Model", AVAILABLE_MODELS, index=0)
        additional_instructions = st.text_area(
            "Additional Instructions", placeholder="E.g., 'Meeting about project planning with Alice, Bob, Charlie.'"
        )
        with st.expander("Advanced: View Full System Prompt"):
            st.code(TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT, language="text")
            # full_prompt = st.text_area("Full System Prompt", 
            #                            value=TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT, 
            #                            height=350,
            #                            disabled=True)
            st.warning("Changing the JSON structure may break the app. View only", icon="⚠️")

        if st.button("Transcribe", disabled=not st.session_state.uploaded_audio):
            update_activity_timestamp()  # Update timestamp on user interaction
            temp_dir = os.path.join("transcription_temp", st.session_state.session_id)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"Cleared temporary transcription directory: {temp_dir}")
            os.makedirs(temp_dir)

            file_ext = os.path.splitext(st.session_state.uploaded_audio.name)[1].lower()
            suffix = file_ext
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(st.session_state.audio_bytes)
                temp_file_path = temp_file.name
            prompt_to_use = additional_instructions if full_prompt == TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT else full_prompt
            try:
                with st.spinner("Transcribing audio (processing 8-minute chunks)..."):
                    transcription_json, uploaded_audio = transcribe_audio_with_diarization(
                        temp_file_path, session_id=st.session_state.session_id, model=selected_model, additional_instructions=prompt_to_use
                    )
                st.session_state.update({
                    "transcription_json": transcription_json,
                    "uploaded_audio": uploaded_audio,  # Update with the API-uploaded file reference
                    "transcription_done": True
                })
                st.success("Transcription completed.")
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
    else:
        st.info("Upload an audio file in Step 1 to enable transcription settings.", icon="ℹ️")

# Highlight Step 2 if active
if current_step == 2:
    st.markdown("""
        <script>
        document.querySelectorAll('[data-testid="stVerticalBlock"] > div')[1].classList.add('active-step');
        </script>
    """, unsafe_allow_html=True)

# Step 3: Review Transcription with Timestamps
with st.container(border=True) as step3_container:
    st.subheader("Step 3: Review Transcription with Timestamps")
    if st.session_state.transcription_done:
        with st.container(height=500):
            for idx, transcript in enumerate(st.session_state.transcription_json):
                if st.button(transcript['timestamp'], key=f"ts_{idx}"):
                    update_activity_timestamp()  # Update timestamp on user interaction
                    st.session_state.selected_time = parse_timestamp_to_seconds(transcript['timestamp'])
                speaker = transcript.get('speaker', 'Unknown Speaker')
                text = transcript.get('text', '[Transcription Missing]')
                st.markdown(f"**{speaker}**: {text}")
                st.markdown("---")
        
        if st.session_state.audio_bytes:
            file_ext = os.path.splitext(st.session_state.uploaded_audio.name)[1].lower()
            audio_format = "audio/wav" if file_ext == ".wav" else "audio/mp3"
            st.audio(st.session_state.audio_bytes, format=audio_format, start_time=st.session_state.selected_time)
    else:
        st.info("Complete transcription in Step 2 to review the results here.", icon="ℹ️")

# Highlight Step 3 if active
if current_step == 3:
    st.markdown("""
        <script>
        document.querySelectorAll('[data-testid="stVerticalBlock"] > div')[2].classList.add('active-step');
        </script>
    """, unsafe_allow_html=True)

# Step 4: Generate Summary
with st.container(border=True) as step4_container:
    st.subheader("Step 4: Generate Summary")
    if st.session_state.transcription_done:
        if st.button("Generate Summary", disabled=not st.session_state.transcription_done):
            update_activity_timestamp()  # Update timestamp on user interaction
            try:
                with st.spinner("Generating summary..."):
                    summary = summarize_transcription(st.session_state.transcription_json, model=selected_model)
                st.session_state.summary = summary
                st.success("Summary generated successfully.")
            except Exception as e:
                st.error(f"Error generating summary: {e}")

        if st.session_state.summary:
            st.subheader("Meeting Summary")
            with st.container(height=500):
                st.write(st.session_state.summary)
            st.info('''
                **What Happens Next?**  \n
                Once your summary is generated, the transcription and summary files will be saved to a folder on the server for integration with RAG Flow.
                After that, download buttons will appear below, allowing you to save the .docx files directly to your device. 
                Files are stored under `transcripts/[selected_folder]` on the server for further processing or sharing!
                ''', icon="ℹ️")
    else:
        st.info("Complete transcription in Step 2 to enable summary generation.", icon="ℹ️")

# Highlight Step 4 if active
if current_step == 4:
    st.markdown("""
        <script>
        document.querySelectorAll('[data-testid="stVerticalBlock"] > div')[3].classList.add('active-step');
        </script>
    """, unsafe_allow_html=True)

# Step 5: Export Transcription and Summary
with st.container(border=True) as step5_container:
    st.subheader("Step 5: Export Transcription and Summary")
    if st.session_state.transcription_done:
        st.info(
            "📂 Files will be saved to the server under `transcripts/[selected_folder]`. "
            "If a file already exists, a unique suffix will be added to avoid overwriting. "
            "Download them to your device using the buttons below.",
            icon="ℹ️"
        )

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

        export_file_name = st.text_input("Enter base file name (without extension)", value="meeting_transcript")

        if st.button("Export Transcription and Summary as DOCX", disabled=not st.session_state.transcription_done):
            update_activity_timestamp()  # Update timestamp on user interaction
            try:
                with st.spinner("Exporting transcription and summary to DOCX..."):
                    transcript_file_name = f"{export_file_name}_transcript.docx"
                    transcript_path = export_transcription_to_docx(
                        st.session_state.transcription_json,
                        output_folder=output_folder,
                        file_name=transcript_file_name
                    )
                    st.session_state.exported_transcript_path = transcript_path
                    
                    if st.session_state.summary:
                        summary_file_name = f"{export_file_name}_summary.docx"
                        summary_path = export_summary_to_docx(
                            st.session_state.summary,
                            output_folder=output_folder,
                            file_name=summary_file_name
                        )
                        st.session_state.exported_summary_path = summary_path
                        st.success(f"🎉 Files exported to server at {output_folder}! Use the buttons below to download to your device.")
                    else:
                        st.success(f"🎉 Transcription exported to server at {output_folder}! Use the button below to download to your device.")
            except Exception as e:
                st.error(f"Error exporting files: {e}")

        # Download buttons for exported files
        if "exported_transcript_path" in st.session_state and st.session_state.exported_transcript_path is not None:
            with st.container():
                st.markdown("**Download Your Files**")
                col1, col2 = st.columns(2)
                with col1:
                    with open(st.session_state.exported_transcript_path, "rb") as file:
                        st.download_button(
                            label="📄 Download Transcription DOCX",
                            data=file,
                            file_name=os.path.basename(st.session_state.exported_transcript_path),
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

        if "exported_summary_path" in st.session_state and st.session_state.exported_summary_path is not None:
            with col2:
                with open(st.session_state.exported_summary_path, "rb") as file:
                    st.download_button(
                        label="📝 Download Summary DOCX",
                        data=file,
                        file_name=os.path.basename(st.session_state.exported_summary_path),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            st.caption("💾 These buttons download the files from the server to your device.")
    else:
        st.info("Complete transcription in Step 2 to enable exporting.", icon="ℹ️")

    # Cleanup option (only show if audio is uploaded)
    if st.session_state.uploaded_audio:
        if st.button("Cleanup Uploaded File"):
            update_activity_timestamp()  # Update timestamp on user interaction
            try:
                temp_dir = os.path.join("transcription_temp", st.session_state.session_id)
                delete_uploaded_file(st.session_state.uploaded_audio.name)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    print(f"Cleaned up user-specific temporary directory: {temp_dir}")
                del st.session_state.uploaded_audio
                st.session_state.transcription_done = False
                st.session_state.transcription_json = None
                st.session_state.audio_bytes = None
                st.session_state.selected_time = 0
                st.session_state.summary = None
                st.session_state.exported_transcript_path = None
                st.session_state.exported_summary_path = None
                clear_session()  # Clear the session ID and related data
                st.success("Uploaded audio file deleted from Gemini servers, local temporary files cleaned up, and session cleared.")
            except Exception as e:
                st.error(f"Error deleting file: {e}")

# Highlight Step 5 if active
if current_step == 5:
    st.markdown("""
        <script>
        document.querySelectorAll('[data-testid="stVerticalBlock"] > div')[4].classList.add('active-step');
        </script>
    """, unsafe_allow_html=True)