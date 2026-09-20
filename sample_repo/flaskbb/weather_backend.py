"""
weather_backend.py
REST/HTTP API endpoints for the weather service.
"""

from flask import Flask, request, jsonify
import weather_service

app = Flask(__name__)


@app.route('/api/weather', methods=['GET'])
def get_weather():
    """
    API endpoint to get weather for a specific location.
    Accepts 'location' as a query parameter.
    """
    location = request.args.get('location')
    
    if not location:
        return jsonify({"error": "Location parameter is required."}), 400

    try:
        weather_data = weather_service.predict_weather(location)
        return jsonify(weather_data), 200
    except ValueError as e:
        return jsonify({"error": str(e)}),
