# src/utils.py
import base64
import re
import imghdr
import streamlit as st
from datetime import datetime, timedelta
import sqlite3
import uuid

# SQLite database file (same as used in ragflow_utils.py)
DB_FILE = "project_ragflow_config.db"

def init_session_db():
    """Initialize the SQLite table for session data."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            last_activity TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_image_mime_type(image_bytes):
    image_type = imghdr.what(None, image_bytes)
    if image_type == "jpeg":
        return "image/jpeg"
    elif image_type == "png":
        return "image/png"
    else:
        raise ValueError(f"Unsupported image type: {image_type}. Please upload a JPEG or PNG image.")

def encode_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")

def split_tables(response_text):
    tables = re.split(r'---TABLE_SEPARATOR---', response_text.strip())
    return [table.strip() for table in tables if table.strip()]

def clean_non_csv_content(content):
    lines = content.replace('\r\n', '\n').splitlines()
    csv_lines = []
    for line in lines:
        if re.match(r'^(Bil|\d+)', line):
            csv_lines.append(line.strip())
    return "\n".join(csv_lines)

def initialize_session():
    """Initialize session ID and timestamp if not already set."""
    init_session_db()
    if 'session_id' not in st.session_state:
        session_id = uuid.uuid4().hex
        st.session_state.session_id = session_id
        current_time = datetime.now()
        st.session_state.last_activity = current_time
        # Store in database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (session_id, last_activity) VALUES (?, ?)", (session_id, current_time))
        conn.commit()
        conn.close()

def update_activity_timestamp():
    """Update the last activity timestamp for the current session."""
    if 'session_id' in st.session_state:
        current_time = datetime.now()
        st.session_state.last_activity = current_time
        # Update in database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET last_activity = ? WHERE session_id = ?", (current_time, st.session_state.session_id))
        conn.commit()
        conn.close()

def check_session_expiry(max_inactivity_days=1):
    """Check if the session has expired and clear it if necessary."""
    if 'session_id' in st.session_state:
        session_id = st.session_state.session_id
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT last_activity FROM sessions WHERE session_id = ?", (session_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            last_activity = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S.%f")
            inactivity_period = datetime.now() - last_activity
            if inactivity_period > timedelta(days=max_inactivity_days):
                clear_session()
                return False
    return True

def clear_session():
    """Clear the session ID and related data."""
    if 'session_id' in st.session_state:
        session_id = st.session_state.session_id
        # Remove from database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()
    # Clear from session state
    keys_to_clear = ['session_id', 'last_activity']
    for key in list(st.session_state.keys()):
        if key in keys_to_clear:
            del st.session_state[key]