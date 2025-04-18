# # pages/2_Meeting_Transcription.py
# import streamlit as st
# import os
# import tempfile
# import shutil
# from src.utils import initialize_session, update_activity_timestamp, check_session_expiry, clear_session
# from src.prompts import TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT
# from src.audio_processor import (
#     transcribe_audio_with_diarization,
#     summarize_transcription,
#     count_audio_tokens,
#     delete_uploaded_file,
#     parse_timestamp_to_seconds,
#     export_transcription_to_docx,
#     export_summary_to_docx
# )

# # Initialize session and check for expiry
# initialize_session()
# if not check_session_expiry(max_inactivity_days=1):
#     st.warning("Session has expired due to inactivity. Starting a new session.")
#     initialize_session()
# update_activity_timestamp()

# st.title("Meeting Transcription and Summarization")
# st.markdown("""
#     <style>
#     div.stButton > button {
#         background-color: #4CAF50;
#         color: white;
#         border: none;
#         padding: 10px 20px;
#         border-radius: 5px;
#         font-size: 16px;
#         cursor: pointer;
#     }
#     div.stButton > button:hover {
#         background-color: #45a049;
#     }
#     div.stDownloadButton > button {
#         background-color: #008CBA;
#         color: white;
#         border: none;
#         padding: 10px 20px;
#         border-radius: 5px;
#         font-size: 16px;
#         cursor: pointer;
#     }
#     div.stDownloadButton > button:hover {
#         background-color: #007bb5;
#     }
#     </style>
# """, unsafe_allow_html=True)
# st.write("Upload an MP3, M4A, or WAV file of a recorded meeting to transcribe it with speaker diarization and generate a summary.")

# # Define available Gemini models
# AVAILABLE_MODELS = [
#     "gemini-2.0-flash",
#     "gemini-2.5-pro-exp-03-25",
#     "gemini-1.5-pro-latest"
# ]

# # Dropdown menu for model selection
# selected_model = st.selectbox("Select LLM Model", AVAILABLE_MODELS, index=0)

# # Session state initialization for other keys
# for key in ["transcription_json", "audio_bytes", "uploaded_audio", "summary", "selected_time", "transcription_done", "exported_transcript_path", "exported_summary_path"]:
#     if key not in st.session_state:
#         st.session_state[key] = None if key != "selected_time" else 0

# # File uploader for MP3, M4A, and WAV
# uploaded_file = st.file_uploader("Upload an MP3, M4A, or WAV file", type=["mp3", "m4a", "wav"], key="uploader_tab3")

# if uploaded_file:
#     st.subheader("Transcription Settings")
#     additional_instructions = st.text_area(
#         "Additional Instructions", placeholder="E.g., 'Meeting about project planning with Alice, Bob, Charlie.'"
#     )
#     with st.expander("Advanced: Edit Full System Prompt"):
#         full_prompt = st.text_area("Full System Prompt", value=TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT, height=200)
#         st.warning("Changing the JSON structure may break the app.", icon="⚠️")

#     if st.button("Transcribe"):
#         update_activity_timestamp()  # Update timestamp on user interaction
#         temp_dir = os.path.join("transcription_temp", st.session_state.session_id)
#         if os.path.exists(temp_dir):
#             shutil.rmtree(temp_dir)
#             print(f"Cleared temporary transcription directory: {temp_dir}")
#         os.makedirs(temp_dir)

#         file_ext = os.path.splitext(uploaded_file.name)[1].lower()
#         suffix = file_ext
        
#         with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
#             temp_file.write(uploaded_file.read())
#             temp_file_path = temp_file.name
#         audio_bytes = uploaded_file.getvalue()
#         prompt_to_use = additional_instructions if full_prompt == TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT else full_prompt
#         try:
#             with st.spinner("Transcribing audio (processing 8-minute chunks)..."):
#                 transcription_json, uploaded_audio = transcribe_audio_with_diarization(
#                     temp_file_path, session_id=st.session_state.session_id, model=selected_model, additional_instructions=prompt_to_use
#                 )
#             st.session_state.update({
#                 "transcription_json": transcription_json, "audio_bytes": audio_bytes,
#                 "uploaded_audio": uploaded_audio, "transcription_done": True
#             })
#             st.success("Transcription completed.")
#         except Exception as e:
#             st.error(f"Error: {e}")
#         finally:
#             if os.path.exists(temp_file_path):
#                 os.unlink(temp_file_path)

# if st.session_state.transcription_done:
#     st.subheader("Transcription with Timestamps")
#     with st.container(height=500):
#         for idx, transcript in enumerate(st.session_state.transcription_json):
#             if st.button(transcript['timestamp'], key=f"ts_{idx}"):
#                 update_activity_timestamp()  # Update timestamp on user interaction
#                 st.session_state.selected_time = parse_timestamp_to_seconds(transcript['timestamp'])
#             speaker = transcript.get('speaker', 'Unknown Speaker')
#             text = transcript.get('text', '[Transcription Missing]')
#             st.markdown(f"**{speaker}**: {text}")
#             st.markdown("---")
    
#     if st.session_state.audio_bytes:
#         file_ext = os.path.splitext(uploaded_file.name)[1].lower()
#         audio_format = "audio/wav" if file_ext == ".wav" else "audio/mp3"
#         st.audio(st.session_state.audio_bytes, format=audio_format, start_time=st.session_state.selected_time)
    
# if st.button("Generate Summary"):
#     update_activity_timestamp()  # Update timestamp on user interaction
#     try:
#         with st.spinner("Generating summary..."):
#             summary = summarize_transcription(st.session_state.transcription_json, model=selected_model)
#         st.session_state.summary = summary
#     except Exception as e:
#         st.error(f"Error generating summary: {e}")

# if st.session_state.summary:
#     with st.container(height=500):
#         st.subheader("Meeting Summary")
#         st.write(st.session_state.summary)
#     st.info('''
#             **What Happens Next?**  \n
#             Once your summary is generated, the transcription and summary files will be saved to a folder on the server for integration with RAG Flow.
#             After that, download buttons will appear below, allowing you to save the .docx files directly to your device. 
#             Files are stored under `transcripts/[selected_folder]` on the server for further processing or sharing!
#             ''', icon="ℹ️")

# st.subheader("Export Transcription and Summary")
# st.info(
#     "📂 Files will be saved to the server under `transcripts/[selected_folder]`. "
#     "If a file already exists, a unique suffix will be added to avoid overwriting. "
#     "Download them to your device using the buttons below.",
#     icon="ℹ️"
# )

# base_transcript_dir = "transcripts"
# if not os.path.exists(base_transcript_dir):
#     os.makedirs(base_transcript_dir)
# existing_folders = [d for d in os.listdir(base_transcript_dir) if os.path.isdir(os.path.join(base_transcript_dir, d))]
# existing_folders.insert(0, "Create New Folder")

# selected_folder_option = st.selectbox("Select or Create Folder", existing_folders)

# if selected_folder_option == "Create New Folder":
#     new_folder_name = st.text_input("Enter new folder name (e.g., Project_X)", value="")
#     output_folder = os.path.join(base_transcript_dir, new_folder_name) if new_folder_name else base_transcript_dir
# else:
#     output_folder = os.path.join(base_transcript_dir, selected_folder_option)

# export_file_name = st.text_input("Enter base file name (without extension)", value="meeting_transcript")

# if st.button("Export Transcription and Summary as DOCX"):
#     update_activity_timestamp()  # Update timestamp on user interaction
#     try:
#         with st.spinner("Exporting transcription and summary to DOCX..."):
#             transcript_file_name = f"{export_file_name}_transcript.docx"
#             transcript_path = export_transcription_to_docx(
#                 st.session_state.transcription_json,
#                 output_folder=output_folder,
#                 file_name=transcript_file_name
#             )
#             st.session_state.exported_transcript_path = transcript_path
            
#             if st.session_state.summary:
#                 summary_file_name = f"{export_file_name}_summary.docx"
#                 summary_path = export_summary_to_docx(
#                     st.session_state.summary,
#                     output_folder=output_folder,
#                     file_name=summary_file_name
#                 )
#                 st.session_state.exported_summary_path = summary_path
#                 st.success(f"🎉 Files exported to server at {output_folder}! Use the buttons below to download to your device.")
#             else:
#                 st.success(f"🎉 Transcription exported to server at {output_folder}! Use the button below to download to your device.")
#     except Exception as e:
#         st.error(f"Error exporting files: {e}")

# if "exported_transcript_path" in st.session_state and st.session_state.exported_transcript_path is not None:
#     with st.container():
#         st.markdown("**Download Your Files**")
#         col1, col2 = st.columns(2)
#         with col1:
#             with open(st.session_state.exported_transcript_path, "rb") as file:
#                 st.download_button(
#                     label="📄 Download Transcription DOCX",
#                     data=file,
#                     file_name=os.path.basename(st.session_state.exported_transcript_path),
#                     mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#                 )

# if "exported_summary_path" in st.session_state and st.session_state.exported_summary_path is not None:
#     with col2:
#         with open(st.session_state.exported_summary_path, "rb") as file:
#             st.download_button(
#                 label="📝 Download Summary DOCX",
#                 data=file,
#                 file_name=os.path.basename(st.session_state.exported_summary_path),
#                 mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#             )
#     st.caption("💾 These buttons download the files from the server to your device.")

# if st.session_state.uploaded_audio and st.button("Cleanup Uploaded File"):
#     update_activity_timestamp()  # Update timestamp on user interaction
#     try:
#         temp_dir = os.path.join("transcription_temp", st.session_state.session_id)
#         delete_uploaded_file(st.session_state.uploaded_audio.name)
#         if os.path.exists(temp_dir):
#             shutil.rmtree(temp_dir)
#             print(f"Cleaned up user-specific temporary directory: {temp_dir}")
#         del st.session_state.uploaded_audio
#         st.session_state.transcription_done = False
#         st.session_state.transcription_json = None
#         st.session_state.audio_bytes = None
#         st.session_state.selected_time = 0
#         st.session_state.summary = None
#         st.session_state.exported_transcript_path = None
#         st.session_state.exported_summary_path = None
#         clear_session()  # Clear the session ID and related data
#         st.success("Uploaded audio file deleted from Gemini servers, local temporary files cleaned up, and session cleared.")
#     except Exception as e:
#         st.error(f"Error deleting file: {e}")

# pages/2_Meeting_Transcription.py
import streamlit as st
import os
import tempfile
import shutil
from src.utils import initialize_session, update_activity_timestamp, check_session_expiry, clear_session
from src.prompts import TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT
from src.audio_processor import (
    transcribe_audio_with_diarization,
    delete_uploaded_file,
    parse_timestamp_to_seconds,
)
from src.text_processor import (
    summarize_transcription,
    export_summary_to_docx,
    export_transcription_to_docx
)

# Initialize session and check for expiry
initialize_session()
if not check_session_expiry(max_inactivity_days=1):
    st.warning("Session has expired due to inactivity. Starting a new session.")
    initialize_session()
update_activity_timestamp()

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

# Step 1: File uploader for MP3, M4A, and WAV
with st.container(border=True):
    st.subheader("Step 1: Upload Audio File")
    uploaded_file = st.file_uploader("Upload an MP3, M4A, or WAV file", type=["mp3", "m4a", "wav"], key="uploader_tab3")

# Step 2: Transcription settings and transcription button (only show if file is uploaded)
with st.container(border=True):
    if uploaded_file:
        st.subheader("Step 2: Transcription Settings")
        selected_model = st.selectbox("Select LLM Model", AVAILABLE_MODELS, index=0)
        additional_instructions = st.text_area(
            "Additional Instructions", placeholder="E.g., 'Meeting about project planning with Alice, Bob, Charlie.'"
        )
        with st.expander("Advanced: Edit Full System Prompt"):
            full_prompt = st.text_area("Full System Prompt", value=TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT, height=200)
            st.warning("Changing the JSON structure may break the app.", icon="⚠️")

        if st.button("Transcribe"):
            update_activity_timestamp()  # Update timestamp on user interaction
            temp_dir = os.path.join("transcription_temp", st.session_state.session_id)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"Cleared temporary transcription directory: {temp_dir}")
            os.makedirs(temp_dir)

            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            suffix = file_ext
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name
            audio_bytes = uploaded_file.getvalue()
            prompt_to_use = additional_instructions if full_prompt == TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT else full_prompt
            try:
                with st.spinner("Transcribing audio (processing 8-minute chunks)..."):
                    transcription_json, uploaded_audio = transcribe_audio_with_diarization(
                        temp_file_path, session_id=st.session_state.session_id, model=selected_model, additional_instructions=prompt_to_use
                    )
                st.session_state.update({
                    "transcription_json": transcription_json, "audio_bytes": audio_bytes,
                    "uploaded_audio": uploaded_audio, "transcription_done": True
                })
                st.success("Transcription completed.")
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

# Step 3: Display transcription (only if transcription is done)
with st.container(border=True):
    if st.session_state.transcription_done:
        st.subheader("Step 3: Review Transcription with Timestamps")
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
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            audio_format = "audio/wav" if file_ext == ".wav" else "audio/mp3"
            st.audio(st.session_state.audio_bytes, format=audio_format, start_time=st.session_state.selected_time)

# Step 4: Generate Summary (only show button if transcription is done)
with st.container(border=True):
    if st.session_state.transcription_done:
        st.subheader("Step 4: Generate Summary")
        if st.button("Generate Summary"):
            update_activity_timestamp()  # Update timestamp on user interaction
            try:
                with st.spinner("Generating summary..."):
                    summary = summarize_transcription(st.session_state.transcription_json, model=selected_model)
                st.session_state.summary = summary
                st.success("Summary generated successfully.")
            except Exception as e:
                st.error(f"Error generating summary: {e}")
    else:
        # Error handling: If user tries to generate summary without uploading and transcribing
        if st.button("Generate Summary", disabled=True):
            st.warning("Please upload an audio file and transcribe it first before generating a summary.", icon="⚠️")

    # Step 5: Display Summary (only if summary is generated)
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

# Step 6: Export Transcription and Summary (only show if transcription is done)
with st.container(border=True):
    if st.session_state.transcription_done:
        st.subheader("Step 5: Export Transcription and Summary")
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

        if st.button("Export Transcription and Summary as DOCX"):
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
        # Error handling: If user tries to export without transcribing
        st.subheader("Step 5: Export Transcription and Summary")
        st.info("Please complete the transcription step before exporting.", icon="ℹ️")

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