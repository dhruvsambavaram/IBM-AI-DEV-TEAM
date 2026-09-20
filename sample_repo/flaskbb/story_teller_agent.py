from .groq_client import GroqClient

class StoryTellerAgent:
    """Agent that asks the Qwen model to generate a story."""

    def __init__(self, client: GroqClient = None):
        self.client = client or GroqClient()

    def tell_story(self, topic: str) -> str:
        """Generate a story about the given topic with at least 300 words."""
        messages = [
            {"role": "system", "content": "You are a creative storyteller. Write a vivid, engaging story."},
            {"role": "user", "content": f"Write a story about {topic} that is at least 300 words long."},
        ]
        return self.client.get_completion(messages)
