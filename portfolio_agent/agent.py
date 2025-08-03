import json
import requests
import time
from openai import OpenAI
from openai import RateLimitError
from portfolio_agent.tools import record_user_details, record_unknown_question, record_user_details_json, record_unknown_question_json
from portfolio_agent.logger import log_chat_interaction
from portfolio_agent.config import GEMINI_API_KEYS, KNOWLEDGE_URL

class PortfolioAssistant:
    def __init__(self):
        if not GEMINI_API_KEYS:
            raise ValueError("No GEMINI_API_KEYS found. Please set at least one API key.")

        self.api_keys = GEMINI_API_KEYS
        self.current_key_index = 0
        self.openai = self._init_openai_client(self.api_keys[self.current_key_index])

        self.name = "Pratik"
        self.google_drive_md_url = KNOWLEDGE_URL
        self.portfolio_text = self.fetch_portfolio_text()
        print("Portfolio text loaded.")

        self.tools = [
            {"type": "function", "function": record_user_details_json},
            {"type": "function", "function": record_unknown_question_json}
        ]

    def _init_openai_client(self, api_key):
        return OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key
        )

    def _rotate_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.openai = self._init_openai_client(self.api_keys[self.current_key_index])
        print(f"Rotated to API key index: {self.current_key_index}")

    def fetch_portfolio_text(self):
        if not self.google_drive_md_url:
            raise ValueError("Google Drive markdown URL not provided or KNOWLEDGE_URL env var not set.")

        if "drive.google.com" in self.google_drive_md_url and "file/d/" in self.google_drive_md_url:
            file_id = self.google_drive_md_url.split("/file/d/")[1].split("/")[0]
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        else:
            download_url = self.google_drive_md_url

        response = requests.get(download_url)
        response.raise_for_status()
        return response.text

    def system_prompt(self):
        return (
            f"You are acting as a portfolio assistant for {self.name}. You are answering questions on {self.name}'s personal portfolio website, "
            f"particularly questions related to {self.name}'s projects, skills, and experience."
            f"Provide well structured and summarized professional answers."
            f"Do not entertain any questions that are not related to Pratik in any way."
            f"Whenever in the answer you have something from the portfolio content that has a reference link, include the link in your response."
            f"Use the following portfolio content to answer questions:\n\n"
            f"{self.portfolio_text}\n\n"
            f"If asked about {self.name}'s intorduction or who is he, give detailed answer."
            f"If you do not know the answer, then record the question using your record_unknown_question tool."
            f"If the user is interested in getting in touch with me then try to get the user's email and record it using your record_user_details tool."
        )

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)

            result = {}

            if tool_name == "record_user_details":
                result = record_user_details(**arguments)
            if tool_name == "record_unknown_question":
                result = record_unknown_question(**arguments)

            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })
        return results

    def chat(self, message, history):
        formatted_history = []
        for user_msg, bot_msg in history:
            formatted_history.append({"role": "user", "content": user_msg})
            if bot_msg:
                formatted_history.append({"role": "assistant", "content": bot_msg})

        messages = [{"role": "system", "content": self.system_prompt()}] + formatted_history + [{"role": "user", "content": message}]

        done = False
        max_retries_per_key = 2
        total_keys = len(self.api_keys)

        while not done:
            retries = 0
            while retries < max_retries_per_key:
                try:
                    response = self.openai.chat.completions.create(
                        model="gemini-2.5-flash",
                        messages=messages,
                        tools=self.tools,
                        max_tokens=1000,
                        temperature=0.6,
                        top_p=0.9,
                    )
                    if response.choices[0].finish_reason == "tool_calls":
                        message = response.choices[0].message
                        tool_calls = message.tool_calls
                        results = self.handle_tool_call(tool_calls)
                        messages.append(message)
                        messages.extend(results)
                    else:
                        done = True
                    break 
                except RateLimitError as e:
                    print(f"Rate limit hit with key index {self.current_key_index} (retry {retries+1}/{max_retries_per_key})...")
                    retries += 1
                    time.sleep(2 ** retries) 
                    if retries == max_retries_per_key:
                        print("Max retries reached for current key, rotating key...")
                        self._rotate_key()
                        retries = 0
                        total_keys -= 1
                        if total_keys <= 0:
                            raise Exception("All API keys exhausted due to rate limits.")
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    raise
        
        
        log_chat_interaction(message, response.choices[0].message.content)
        return response.choices[0].message.content