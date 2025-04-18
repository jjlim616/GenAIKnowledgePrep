# src/ragflow_utils.py
import sqlite3
from cryptography.fernet import Fernet
import requests
import os
from config import ENCRYPTION_KEY

# Initialize encryption (in production, store the key securely)
fernet = Fernet(ENCRYPTION_KEY)

# SQLite database file
DB_FILE = "project_ragflow_config.db"

def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_ragflow_config (
            project_name TEXT PRIMARY KEY,
            encrypted_api_key TEXT NOT NULL,
            knowledge_base_id TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_project_config(project_name, api_key, knowledge_base_id=None):
    """Save a project configuration to the database."""
    encrypted_api_key = fernet.encrypt(api_key.encode()).decode()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO project_ragflow_config (project_name, encrypted_api_key, knowledge_base_id)
        VALUES (?, ?, ?)
    """, (project_name, encrypted_api_key, knowledge_base_id))
    conn.commit()
    conn.close()

def delete_project_config(project_name):
    """Delete a project configuration from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM project_ragflow_config WHERE project_name = ?", (project_name,))
    conn.commit()
    conn.close()

def get_project_config(project_name):
    """Retrieve a project configuration from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT encrypted_api_key, knowledge_base_id FROM project_ragflow_config WHERE project_name = ?", (project_name,))
    result = cursor.fetchone()
    conn.close()
    if result:
        encrypted_api_key, knowledge_base_id = result
        api_key = fernet.decrypt(encrypted_api_key.encode()).decode()
        return api_key, knowledge_base_id
    return None, None

def get_all_projects():
    """Get all project names from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT project_name FROM project_ragflow_config")
    projects = [row[0] for row in cursor.fetchall()]
    conn.close()
    return projects

def fetch_knowledge_bases(api_key, ragflow_base_url):
    """Fetch knowledge bases from RAGFlow."""
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{ragflow_base_url}/api/v1/datasets", headers=headers)
        response.raise_for_status()
        data = response.json()
        if data["code"] == 0:
            return data["data"]
        else:
            return []
    except Exception as e:
        return []

def push_to_ragflow(api_key, knowledge_base_id, file_path, ragflow_base_url):
    """Push a file to a RAGFlow knowledge base."""
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            response = requests.post(
                f"{ragflow_base_url}/api/v1/datasets/{knowledge_base_id}/documents",
                headers=headers,
                files=files
            )
        response.raise_for_status()
        data = response.json()
        if data["code"] == 0:
            return True, data["data"][0]["id"]
        else:
            return False, None
    except Exception as e:
        return False, None

def parse_document(api_key, knowledge_base_id, document_id, ragflow_base_url):
    """Parse a document in RAGFlow to chunk it into embeddings."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{ragflow_base_url}/api/v1/datasets/{knowledge_base_id}/chunks",
            headers=headers,
            json={"document_ids": [document_id]}
        )
        response.raise_for_status()
        data = response.json()
        if data["code"] == 0:
            return True
        else:
            return False
    except Exception as e:
        return False

def list_transcript_files(transcript_folder):
    """Recursively list all DOCX files in the transcript folder and its subfolders."""
    docx_files = []
    for root, dirs, files in os.walk(transcript_folder):
        for file in files:
            if file.endswith(".docx"):
                # Get the relative path from the transcript_folder
                relative_path = os.path.relpath(os.path.join(root, file), transcript_folder)
                docx_files.append(relative_path)
    return docx_files