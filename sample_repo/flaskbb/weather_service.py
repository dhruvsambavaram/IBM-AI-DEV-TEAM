"""
weather_service.py
Core weather forecast logic and input validation.
"""

import re
import random


def validate_location(location: str) -> dict:
    """
    Validates the location input.
    Returns a dictionary with 'valid' boolean and 'error' message if invalid.
    """
    if not location or not isinstance(location, str):
        return {"valid": False, "error": "Location cannot be empty or non-string."}
    
    location_stripped = location.strip()
    if not location_stripped:
        return {"valid": False, "error": "Location cannot be empty."}
        
    # Basic regex to ensure it looks like a city name (letters, spaces, numbers, hyphens, dots)
    # Adjusting for common city name patterns
    if not re.match(r'^[A-Za-z0-9 .-]+$', location_stripped):
        return {"valid": False, "error": "Location contains invalid characters."}
        
    return {"valid": True, "location": location_stripped}


def predict_weather(location: str) -> dict:
    """
    Predicts weather based on the provided location.
    Uses a simulated data source for demonstration purposes.
    """
    validation = validate_location(location)
    if not validation["valid"]:
        raise ValueError(validation["error"])
    
    # Simulate data retrieval and prediction
    conditions = ["Sunny", "Cloudy", "Rainy", "Snowy", "Windy", "Partly Cloudy"]
    condition = random.choice(conditions)
    temperature = random.randint(-10, 40)
    humidity = random.randint(20, 100)
    wind_speed = random.randint(0, 50)
    
    return {
        "location": validation["location"],
        "condition": condition,
        "temperature_c": temperature,
        "humidity_percent": humidity,
        "wind_speed_kmh": wind_speed
    }


if __name__ == "__main__":
    try:
        result = predict_weather("New York")
        print(result)
    except ValueError as e:
        print(f"Error: {e}")
