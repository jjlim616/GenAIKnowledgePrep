# Meeting Transcription and Analysis Platform

## Overview
This project is a Streamlit-based web application designed to streamline the processing, transcription, summarization, and analysis of meeting recordings and documents. It provides tools to transcribe audio files, generate structured summaries, extract tables from diagrams, and integrate transcripts with RAGFlow for knowledge management. The platform is tailored for technical teams, supporting User Requirements Specification (URS), Software Requirements Specification (SRS), and System Design Specification (SDS) workflows, with a focus on actionable insights and documentation.

## Features
- **Meeting Transcription**: Upload MP3, M4A, or WAV files to transcribe meetings with speaker diarization, using Gemini models for accurate transcription and timestamped output.
- **Summary Generation**: Generate structured summaries from transcripts or uploaded DOCX/PDF files, with customizable templates (Technical, URS, General, Executive Overview) and additional focus instructions.
- **Diagram Analysis**: Upload images of hierarchy diagrams, ERDs, or use case diagrams to generate tables in CSV format, supporting Malay-language output and refinement based on user feedback.
- **RAGFlow Integration**: Push transcribed and summarized DOCX files to RAGFlow knowledge bases for embedding and retrieval, with project and API key management.
- **Session Management**: Maintains user sessions with automatic expiry after one day of inactivity, ensuring secure and efficient data handling.
- **Export Options**: Export transcriptions and summaries as DOCX or Markdown files, with folder organization and download capabilities.

## Project Structure
```
├── .env                       # Environment variables (API keys)
├── config.py                  # Configuration loading from .env
├── pages/
│   ├── 1_Generate_Tables.py   # Diagram analysis and table generation
│   ├── 2_Meeting_Transcription.py  # Audio transcription and summarization
│   ├── 3_Transcript_Processing.py  # Transcript summarization from DOCX/PDF
│   ├── 4_Push_Transcripts_to_RAGFlow.py  # RAGFlow integration
├── src/
│   ├── audio_processor.py     # Audio transcription and conversion logic
│   ├── prompts.py             # Prompt templates for transcription and summarization
│   ├── ragflow_utils.py       # RAGFlow API utilities
│   ├── table_generator.py     # Table generation from diagrams
│   ├── text_processor.py      # Text extraction and summary export
│   ├── utils.py               # General utilities (session, image handling)
├── transcripts/               # Output folder for exported files
├── transcription_logs/        # Logs for transcription processes
├── transcription_temp/        # Temporary files for audio processing
├── project_ragflow_config.db  # SQLite database for session and project data
├── requirements.txt           # Python dependencies
```

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/GenAIKnowledgePrep.git
   cd GenAIKnowledgePrep
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv .venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Ensure you have Pandoc installed for DOCX conversion:
   - On Ubuntu: `sudo apt-get install pandoc`
   - On macOS: `brew install pandoc`
   - On Windows: Download and install from [Pandoc releases](https://github.com/jgm/pandoc/releases)

4. **Configure Environment**:
   Create a `.env` file in the root directory with the following:
   ```
   GEMINI_API_KEY=your-gemini-api-key
   OPENAI_API_KEY=your-openai-api-key
   RAGFLOW_BASE_URL=your-ragflow-base-url
   ```
   Update `config.py` to load variables from `.env` using a library like `python-dotenv`. Example:
   ```python
   from dotenv import load_dotenv
   import os
   load_dotenv()
   GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
   OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
   RAGFLOW_BASE_URL = os.getenv("RAGFLOW_BASE_URL")
   ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
   ```

5. **Run the Application**:
   ```bash
   streamlit run app.py
   ```
   Access the app at `http://localhost:8501`.

## Usage
1. **Meeting Transcription**:
   - Navigate to the "Meeting Transcription" page.
   - Upload an audio file (MP3, M4A, WAV).
   - Configure transcription settings (model, additional instructions).
   - Review the transcription, generate a summary, and export to DOCX.

2. **Transcript Processing**:
   - Go to the "Transcript Processing" page.
   - Upload a DOCX or PDF transcript.
   - Select a summary template and model, add focus instructions, and generate a summary.
   - Export the summary as DOCX or Markdown.

3. **Diagram Analysis**:
   - Visit the "Generate Tables" page.
   - Upload an image (JPG, PNG) of a hierarchy diagram, ERD, or use case diagram.
   - Provide a custom prompt (optional) and generate tables in Malay.
   - Refine tables with feedback and download as CSV.

4. **RAGFlow Integration**:
   - Access the "Push Transcripts to RAGFlow" page.
   - Set up a project with a name and RAGFlow API key.
   - Select a knowledge base and push DOCX files from the `transcripts` folder.

## Dependencies
- Python 3.11.9
- Streamlit
- Pandas
- Pydub
- Google Generative AI (Gemini)
- OpenAI
- PyPandoc
- Docx2txt
- PyMuPDF (fitz)
- Cryptography
- SQLite3
- Requests
- Python-dotenv
- See `requirements.txt` for a complete list.

## Notes
- **API Keys**: Ensure valid Gemini, OpenAI, and RAGFlow API keys are configured in `.env`.
- **File Storage**: Transcripts and summaries are stored in the `transcripts` folder with subfolder support to avoid overwrites.
- **Session Expiry**: Sessions expire after 24 hours of inactivity, clearing temporary files and session data.
- **Error Handling**: The application includes robust error handling for file uploads, API calls, and document processing.
- **Language Support**: Transcription supports Malay speech; table generation outputs in Malay as per prompt requirements.

## Contributing
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact
For issues or inquiries, please open an issue on the GitHub repository or contact the project maintainer at [jjlim616@hotmail.com].
