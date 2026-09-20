from .groq_client import GroqClient
from .story_teller_agent import StoryTellerAgent

class StoryRefinerAgent:
    """Agent that refines a given story for grammar, style, and flow."""

    def __init__(self, client: GroqClient = None):
        self.client = client or GroqClient()

    def refine_story(self, story: str) -> str:
        """Refine the provided story."""
        messages = [
            {"role": "system", "content": "You are an expert editor. Improve the grammar, style, and narrative flow of the following story."},
            {"role": "user", "content": story},
        ]
        return self.client.get_completion(messages)

def generate_and_refine(topic: str) -> str:
    """Generate a story on the given topic and then refine it."""
    teller = StoryTellerAgent()
    raw_story = teller.tell_story(topic)
    refiner = StoryRefinerAgent()
    return refiner.refine_story(raw_story)
