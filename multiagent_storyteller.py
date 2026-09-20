"""
Multiagent Storyteller System using Groq API
"""

import os
from typing import Dict, Any

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class MultiagentStoryteller:
    """
    A multiagent system that uses the Groq API to generate stories
    from a Qwen model acting as a storyteller.
    """

    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize the Groq API client and configuration.

        Args:
            api_key: Groq API key. If not provided, reads from GROQ_API_KEY env var.
            model: Model identifier. Defaults to 'llama-3.1-8b-instant' as 
                   placeholder for Qwen model in Groq context or specific qwen model if available.
        """
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key and GROQ_AVAILABLE:
            raise ValueError("Groq API key is required. Provide api_key or set GROQ_API_KEY environment variable.")

        self.model = model or "llama-3.1-8b-instant"

        # System prompt instructing the model to act as a storyteller persona
        self.system_prompt = (
            "You are a highly skilled and creative storyteller. "
            "You excel at crafting engaging narratives with vivid descriptions, "
            "compelling characters, and unexpected plot twists. "
            "Always stay in character as the storyteller when generating content."
        )

        self.client = None
        if GROQ_AVAILABLE and self.api_key:
            self.client = Groq(api_key=self.api_key)

    def tell_story(self, prompt: str, temperature: float = 1.1) -> Dict[str, Any]:
        """
        Generate a story using the Groq API.

        Args:
            prompt: User input or theme for the story.
            temperature: Sampling temperature for creativity.

        Returns:
            A dictionary containing the response status and story content.
        """
        if not self.client:
            return {
                "success": False,
                "error": "Groq client is not initialized. Check API key and dependencies."
            }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=1024
            )

            story_content = response.choices[0].message.content

            return {
                "success": True,
                "story": story_content,
                "model": self.model
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}"
            }
if __name__ == "__main__":
    storyteller = MultiagentStoryteller()
    result = storyteller.tell_story("Once upon a time in a magical forest...")
    if result["success"]:
        print(result["story"])
    else:
        print(f"Error: {result['error']}")
