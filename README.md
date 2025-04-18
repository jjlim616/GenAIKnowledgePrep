# GenAIKnowledgePrep
AI pipeline transforming meeting audio &amp; diagrams into RAG-ready tables, transcripts, and summaries.

AI pipeline transforming meeting audio & diagrams into RAG-ready tables, transcripts, and summaries. This tool uses various generative AI models to process unstructured and semi-structured inputs, making the knowledge accessible via systems like RAGFlow.

## Overview

This project aims to streamline the process of extracting valuable information from common business artifacts like meeting recordings and technical diagrams. It bridges the gap between raw data and actionable, queryable knowledge within a Retrieval-Augmented Generation (RAG) system. The application provides a multi-page Streamlit interface for different processing tasks.

## Key Features

*   **Diagram-to-Table Generation:**
    *   Upload images of Hierarchy, ERD, or Use Case diagrams.
    *   Uses GPT-4.1 Vision to analyze diagrams based on configurable system prompts.
    *   Generates structured tables (CSV format, pipe-delimited) representing the diagram's content.
    *   Supports iterative refinement based on user feedback.
*   **Meeting Transcription & Summarization:**
    *   Upload MP3, M4A, or WAV audio files.
    *   Transcribes audio using Gemini models, including speaker diarization (Speaker A, Speaker B, etc.).
    *   Handles large files by chunking.
    *   Generates meeting summaries based on the transcription.
*   **Advanced Summarization:**
    *   Process existing transcript documents (DOCX, PDF).
    *   Utilizes various LLMs (GPT-4.1, Gemini, Grok) for summarization.
    *   Offers multiple prompt templates (Technical, URS, General, Overview) for tailored summaries.
    *   Supports optional reasoning mode (for compatible models like Grok-3-mini, Gemini 2.5 Pro) to show the AI's thought process.
    *   Allows customization of prompts and adding specific focus instructions.
    *   Exports summaries in DOCX and Markdown formats.
*   **RAGFlow Integration:**
    *   Configure RAGFlow projects and API keys securely (using encryption and SQLite).
    *   Select generated transcript/summary DOCX files.
    *   Push selected documents directly to a chosen RAGFlow knowledge base via the API.
    *   Initiate document parsing within RAGFlow.
*   **User Session Management:** Includes basic inactivity tracking and session expiry.
