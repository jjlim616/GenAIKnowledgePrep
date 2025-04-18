# src/audio_processor.py
# Standard library imports
import json
import os
import time
import uuid
import tempfile

# Third-party imports
import pypandoc
from docx import Document
from pydub import AudioSegment
from google import genai

# Local imports
from config import GEMINI_API_KEY
from src.prompts import TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT, SUMMARY_DEFAULT_SYSTEM_PROMPT, GENERAL_SUMMARY_PROMPT

# Configure Gemini API
client = genai.Client(api_key=GEMINI_API_KEY)


def convert_m4a_to_mp3(input_path, output_path):
    """Convert an m4a file to mp3 using pydub."""
    try:
        audio = AudioSegment.from_file(input_path, format="m4a")
        audio.export(output_path, format="mp3")
        print(f"Converted {input_path} to {output_path}")
        return output_path
    except Exception as e:
        raise Exception(f"Failed to convert m4a to mp3: {e}")

def transcribe_audio_with_diarization(audio_path, session_id, model="gemini-2.0-flash", additional_instructions="", max_retries=3, retry_delay=5):
    """Transcribe audio with diarization, splitting into 8-min chunks with 30s overlap."""
    full_prompt = TRANSCRIPTION_DEFAULT_SYSTEM_PROMPT
    if additional_instructions:
        full_prompt += f"\n\nAdditional Instructions: {additional_instructions}"

    log_dir = os.path.join("transcription_logs", session_id)
    temp_dir = os.path.join("transcription_temp", session_id)
    for directory in [log_dir, temp_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    file_ext = os.path.splitext(audio_path)[1].lower()
    temp_audio_path = audio_path
    if file_ext == ".m4a":
        temp_mp3_path = os.path.join(temp_dir, f"converted_{uuid.uuid4().hex}.mp3")
        temp_audio_path = convert_m4a_to_mp3(audio_path, temp_mp3_path)
    
    if file_ext == ".wav":
        audio = AudioSegment.from_wav(temp_audio_path)
    else:
        audio = AudioSegment.from_mp3(temp_audio_path)
    
    chunks = []
    start_time = 0
    audio_length = len(audio)
    chunk_length_ms = 480000
    overlap_ms = 0
    
    while start_time < audio_length:
        end_time = min(start_time + chunk_length_ms, audio_length)
        chunks.append((start_time // 1000, end_time // 1000))
        start_time = end_time - overlap_ms if end_time < audio_length else audio_length
    
    all_transcriptions = []
    uploaded_files = []
    
    for chunk_idx, (start_sec, end_sec) in enumerate(chunks):
        temp_file = os.path.join(temp_dir, f"{session_id}_chunk_{chunk_idx}_transcription.json")
        if os.path.exists(temp_file):
            print(f"Loading previously transcribed chunk {chunk_idx} from {temp_file}")
            with open(temp_file, "r", encoding="utf-8") as f:
                chunk_transcription = json.load(f)
            if chunk_transcription and chunk_transcription[0].get("text") == "[Transcription Failed After Retries]":
                print(f"Chunk {chunk_idx} previously failed. Retrying...")
            else:
                all_transcriptions.extend(chunk_transcription)
                continue
        
        success = False
        for attempt in range(max_retries):
            start_ms = start_sec * 1000
            end_ms = end_sec * 1000
            chunk = audio[start_ms:end_ms]
            temp_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            chunk.export(temp_file_path, format="mp3")
            
            try:
                audio_file = client.files.upload(file=temp_file_path)
                uploaded_files.append(audio_file)
                response = client.models.generate_content(
                    model=model,
                    contents=[full_prompt, audio_file],
                    config={"response_mime_type": "application/json"}
                )
                log_file = os.path.join(log_dir, f"{session_id}_chunk_{chunk_idx}_start_{start_sec//60:02d}{start_sec%60:02d}_end_{end_sec//60:02d}{end_sec%60:02d}_attempt_{attempt}.json")
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"Saved raw response for chunk {chunk_idx} (attempt {attempt}) to {log_file}")
                
                chunk_transcription = json.loads(response.text)
                for entry in chunk_transcription:
                    if 'timestamp' not in entry:
                        entry['timestamp'] = f"{format_time(start_sec)} - {format_time(start_sec + 1)}"
                    if 'speaker' not in entry:
                        entry['speaker'] = "Unknown Speaker"
                    if 'text' not in entry:
                        entry['text'] = "[Transcription Missing]"
                    start = parse_timestamp_to_seconds(entry["timestamp"].split(" - ")[0])
                    end = parse_timestamp_to_seconds(entry["timestamp"].split(" - ")[1])
                    entry["timestamp"] = f"{format_time(start_sec + start)} - {format_time(start_sec + end)}"
                
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(chunk_transcription, f, ensure_ascii=False, indent=2)
                print(f"Saved successful transcription for chunk {chunk_idx} to {temp_file}")
                
                all_transcriptions.extend(chunk_transcription)
                success = True
                break
            
            except json.JSONDecodeError as e:
                print(f"Failed to parse transcription for chunk {chunk_idx} (attempt {attempt}): {e}")
                if attempt == max_retries - 1:
                    print(f"Max retries reached for chunk {chunk_idx}. Skipping this chunk.")
                    chunk_transcription = [{
                        "timestamp": f"{format_time(start_sec)} - {format_time(end_sec)}",
                        "speaker": "Unknown Speaker",
                        "text": "[Transcription Failed After Retries]"
                    }]
                    all_transcriptions.extend(chunk_transcription)
                    with open(temp_file, "w", encoding="utf-8") as f:
                        json.dump(chunk_transcription, f, ensure_ascii=False, indent=2)
                    break
                print(f"Retrying chunk {chunk_idx} in {retry_delay} seconds...")
                time.sleep(retry_delay)
            
            except Exception as e:
                print(f"Unexpected error for chunk {chunk_idx} (attempt {attempt}): {e}")
                if attempt == max_retries - 1:
                    print(f"Max retries reached for chunk {chunk_idx}. Skipping this chunk.")
                    chunk_transcription = [{
                        "timestamp": f"{format_time(start_sec)} - {format_time(end_sec)}",
                        "speaker": "Unknown Speaker",
                        "text": "[Transcription Failed After Retries]"
                    }]
                    all_transcriptions.extend(chunk_transcription)
                    with open(temp_file, "w", encoding="utf-8") as f:
                        json.dump(chunk_transcription, f, ensure_ascii=False, indent=2)
                    break
                print(f"Retrying chunk {chunk_idx} in {retry_delay} seconds...")
                time.sleep(retry_delay)
            
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
    
    # Clean up converted file if it was created
    # Clean up temporary transcription files after successful completion
    # Comment out for debugging
    # for chunk_idx in range(len(chunks)):
    #     temp_file = os.path.join(temp_dir, f"chunk_{chunk_idx}_transcription.json")
    #     if os.path.exists(temp_file):
    #         os.unlink(temp_file)
    #         print(f"Cleaned up temporary file: {temp_file}")
    return all_transcriptions, uploaded_files[0] if uploaded_files else None

# def summarize_transcription(transcription_json, model="gemini-2.0-flash"):
#     full_prompt = SUMMARY_DEFAULT_SYSTEM_PROMPT
#     transcription_text = "\n".join(
#         f"[{entry['timestamp']}] {entry['speaker']}: {entry['text']}"
#         for entry in transcription_json
#     )
#     response = client.models.generate_content(
#         model=model,
#         contents=[full_prompt, transcription_text]
#     )
#     return response.text



def count_audio_tokens(audio_file, model="gemini-2.0-flash"):
    response = client.models.count_tokens(model=model, contents=[audio_file])
    return response.total_tokens

def delete_uploaded_file(file_name):
    client.files.delete(name=file_name)

def parse_timestamp_to_seconds(timestamp):
    """Convert MM:SS or HH:MM:SS format to start seconds."""
    try:
        parts = timestamp.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            return 0
    except:
        return 0

def format_time(seconds):
    """Convert seconds to MM:SS format."""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

