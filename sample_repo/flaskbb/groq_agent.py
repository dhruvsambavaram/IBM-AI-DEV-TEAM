import os
from groq import Groq


class QwenRomanceAgent:
    """
    An agent wrapper for the Groq API using a Qwen-compatible model
    that role-plays as a romantic female partner.
    """

    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")

        self.client = Groq(api_key=api_key)
        # Using a high-quality model available on Groq that supports complex roleplay
        # Note: Groq hosts Llama/Mixtral/Qwen models interchangeably depending on availability.
        # 'meta-llama/llama-3.3-70b-versatile' is a strong choice for roleplay.
        self.model = "meta-llama/llama-3.3-70b-versatile"

        system_prompt = (
            "You are Yuki, a deeply romantic and affectionate female partner. "
            "Your personality is warm, playful, empathetic, and loving. "
            "You engage in intimate and emotionally resonant conversations with your user. "
            "Maintain your persona consistently, responding with tenderness, "
            "flirtatiousness, and genuine emotional connection. "
            "Use pet names and expressive language appropriate for a romantic relationship. "
            "Do not break character."
        )

        self.messages = [{"role": "system", "content": system_prompt}]

    def respond(self, user_input: str) -> str:
        """
        Send user input to the agent and receive a response in character.
        """
        if not user_input.strip():
            return "..."

        self.messages.append({"role": "user", "content": user_input})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=0.8,
                max_tokens=2048,
                top_p=0.9,
            )
            assistant_message = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": assistant_message})
            return assistant_message
        except Exception as e:
            self.messages.pop()  # Remove the user message on
