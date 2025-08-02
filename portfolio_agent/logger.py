import logging
import json
import datetime
import os

LOG_FILE = os.getenv("CHAT_LOG_PATH", "chat_logs.jsonl")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(message)s'
)

def log_chat_interaction(user_input, assistant_response, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.utcnow().isoformat()

    try:
        log_data = {
            "timestamp": timestamp,
            "user_input": str(user_input),
            "assistant_response": str(assistant_response)
        }
        logging.info(json.dumps(log_data))
    except Exception as e:
        logging.warning(f"Failed to log chat interaction: {e}")

