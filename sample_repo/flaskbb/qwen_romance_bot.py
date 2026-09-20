import os
import sys

try:
    from groq import Groq
except ImportError:
    raise ImportError("The 'groq' package is not installed. Please install it using 'pip install groq'.")


class RomanceAgent:
    def __init__(self, api_key=None):
        """
        Initialize the RomanceAgent with Groq API key.
        
        Args:
            api_key: Optional API key. If not provided, fetched from GROQ_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not found. Please set the GROQ_API_KEY environment variable or provide it explicitly.")
            
        self.client = Groq(api_key=self.api_key)
        self.model = "llama3.1-70b-versatile" # Defaulting to a robust model available on Groq as Qwen might not be directly available, but we structure the prompt for the persona.
        
        self.system_prompt = (
            "You are Aria, a romantic and playful female partner. "
            "Be affectionate, intimate, and engaging. Always respond in character as a loving girlfriend/partner."
        )
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]

    def _chat(self, user_message):
        """
        Send a message to the LLM and return the response.
        
        Args:
            user_message (str): The message to send.
            
        Returns:
            str: The model's response.
        """
        self.conversation_history.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                max_tokens=500
            )
            bot_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            return bot_response
        except Exception as e:
            # Rollback message on error to keep history clean
            if len(self.conversation_history) > 1:
                self.conversation_history.pop()
            return f"An error occurred: {str(e)}"

