import os
import requests

class GroqClient:
    """Simple wrapper around Groq's chat completion API for the Qwen model."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set and no api_key provided.")
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def get_completion(self, messages, model: str = "qwen"):
        """Send a list of messages to the API and return the assistant's reply text."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
        }
        response = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
