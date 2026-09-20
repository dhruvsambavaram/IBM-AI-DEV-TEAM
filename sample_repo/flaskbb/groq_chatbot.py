import os
import json
import time
from typing import Dict, Any, Optional

try:
    from groq import Groq
except ImportError:
    Groq = None

class GroqAPIHandler:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('GROQ_API_KEY', '')
        self.client = None
        if Groq and self.api_key:
            self.client = Groq(api_key=self.api_key)

    def validate_message(self, message: str) -> Dict[str, Any]:
        if not isinstance(message, str):
            return {
                "valid": False,
                "error": {
                    "code": "INVALID_FORMAT",
                    "message": "Message must be a string"
                }
            }
        
        if not message.strip():
            return {
                "valid": False,
                "error": {
                    "code": "EMPTY_MESSAGE",
                    "message": "Message cannot be empty"
                }
            }
            
        if len(message) > 4096:
            return {
                "valid": False,
                "error": {
                    "code": "MESSAGE_TOO_LONG",
                    "message": "Message exceeds maximum length of 4096 characters"
                }
            }
            
        return {"valid": True, "error": None}

    def process_message(self, message: str, user_session_id: str = "default") -> Dict[str, Any]:
        validation = self.validate_message(message)
        if not validation["valid"]:
            return validation["error"]

        if not self.client:
            return {
                "status": "error",
                "error": {
                    "code": "API_NOT_CONFIGURED",
                    "message": "Groq API client not configured"
                }
            }

        try:
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=2048
            )
            
            reply = response.choices[0].message.content
            
            return {
                "status": "success",
                "data": {
                    "message": reply,
                    "session_id": user_session_id,
                    "timestamp": time.time()
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": {
                    "code": "API_REQUEST_FAILED",
                    "message": f"Failed to process request: {str(e)}"
                }
            }

    def get_standardized_response(self, data: Any) -> str:
        return json.dumps(data, indent=2)

if __name__ == "__main__":
    handler
