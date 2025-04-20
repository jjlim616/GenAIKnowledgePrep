# app.py
import streamlit as st

# Set page configuration
st.set_page_config(page_title="Meeting and Diagram Analysis App", layout="wide")

st.title("Welcome to the Meeting and Diagram Analysis App")
st.write("""
This app provides two main functionalities:

- **Generate Tables**: Upload a diagram (e.g., use case or hierarchy diagram) to analyze it and generate tables in CSV format.
- **Meeting Transcription**: Upload an MP3 file of a recorded meeting to transcribe it with speaker diarization and generate a summary.
- **Transcript Processing & Summaries**: Process the transcribed text to generate summaries and insights using various models and templates.
- **RagFlow Intergration**: Push transcripts and summary to RAGFlow for further analysis and storage.
         
Use the sidebar to navigate to the desired page.
""")