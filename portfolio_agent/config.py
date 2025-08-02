import os
from dotenv import load_dotenv

load_dotenv(override=True)

PUSHBULLET_API_KEY = os.getenv("PUSHBULLET_API_KEY")
KNOWLEDGE_URL = os.getenv("KNOWLEDGE_URL")

GEMINI_API_KEYS = []

for i in range(1, 5):
    key = os.getenv(f"GEMINI_API_KEY_{i}")
    if key:
        GEMINI_API_KEYS.append(key)

if not GEMINI_API_KEYS:
    raise ValueError("No GEMINI_API_KEY_* environment variables found. Please set at least one API key.")