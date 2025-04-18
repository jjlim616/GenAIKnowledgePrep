# config.py
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Path to store the encryption key (optional, if you want to persist it in a separate file)
ENCRYPTION_KEY_FILE = "encryption_key.txt"

# RAGFlow base URL
RAGFLOW_BASE_URL = os.getenv("RAGFLOW_BASE_URL")

# Load or generate the encryption key
def load_or_generate_key():
    """Load the encryption key from a file or generate a new one if it doesn't exist."""
    if os.path.exists(ENCRYPTION_KEY_FILE):
        with open(ENCRYPTION_KEY_FILE, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(ENCRYPTION_KEY_FILE, "wb") as f:
            f.write(key)
        return key

# Encryption key (loaded or generated)
ENCRYPTION_KEY = load_or_generate_key()