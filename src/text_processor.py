# src/text_processor.py
import io
import os
import uuid
from docx import Document
import streamlit as st
import docx2txt
import fitz
import pypandoc

from src.prompts import GENERAL_SUMMARY_PROMPT
from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)   


def summarize_transcription(transcription_input, model="gemini-2.0-flash", custom_prompt=None):
    """
    Generate a summary from transcription data using Gemini API.
    
    Args:
        transcription_input: The transcription data as JSON or plain text
        model: The Gemini model to use for summarization
        custom_prompt: Optional custom system prompt for summarization
        
    Returns:
        The generated summary text
    """
    full_prompt = custom_prompt if custom_prompt else GENERAL_SUMMARY_PROMPT
    
    # Handle different input types
    if isinstance(transcription_input, list):
        # JSON format from direct transcription
        transcription_text = "\n".join(
            f"[{entry['timestamp']}] {entry['speaker']}: {entry['text']}"
            for entry in transcription_input
        )
    elif isinstance(transcription_input, str):
        # Already text from DOCX/PDF extraction
        transcription_text = transcription_input
    else:
        raise ValueError("Unsupported transcription input format")
    
    response = client.models.generate_content(
        model=model,
        contents=[full_prompt, transcription_text]
    )
    return response.text

def export_transcription_to_docx(transcription_json, output_folder="transcripts", file_name="transcript.docx"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    output_path = os.path.join(output_folder, file_name)
    if os.path.exists(output_path):
        base, ext = os.path.splitext(file_name)
        file_name = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
        output_path = os.path.join(output_folder, file_name)
    doc = Document()
    doc.add_heading("Meeting Transcription", level=1)
    for entry in transcription_json:
        doc.add_paragraph(f"[{entry['timestamp']}] {entry['speaker']}: {entry['text']}")
    doc.save(output_path)
    return output_path

def export_summary_to_docx(summary, output_folder="transcripts", file_name="summary.docx"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    output_path = os.path.join(output_folder, file_name)
    if os.path.exists(output_path):
        base, ext = os.path.splitext(file_name)
        file_name = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
        output_path = os.path.join(output_folder, file_name)

    # Prepare the Markdown content
    markdown_content = "# Meeting Summary\n\n" + summary

    try:
        # Use pypandoc to convert Markdown to DOCX
        pypandoc.convert_text(
            markdown_content,
            'docx',
            format='md',
            outputfile=output_path
        )
        print(f"Converted Markdown to DOCX: {output_path}")
    except OSError as e:
        raise Exception(f"Pandoc conversion failed: {str(e)}. Please ensure Pandoc is installed on your system.")

    return output_path

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
                text += page.get_text("text") + "\n" # Added newline
            return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return None