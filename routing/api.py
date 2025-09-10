"""
Flask API for train routing service.

Provides REST endpoints to get routes between stations.
"""

import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

# Add the routing module to the path
sys.path.append(str(Path(__file__).parent))
from routing import DATA_DIR_DEFAULT, getRoute, load_stops

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

@app.route('/api/route', methods=['GET'])
def get_route_api():
    """
    Get route between two stations via GET request.
    
    Query parameters:
        - from: Origin station (stop_id or partial station name)
        - to: Destination station (stop_id or partial station name)
        - time: Optional departure time (HH:MM:SS format, default: "08:00:00")
    
    Example:
        GET /api/route?from=CAGLIARI&to=OLBIA
        GET /api/route?from=CAGLIARI&to=OLBIA&time=09:30:00
    """
    try:
        # Get parameters from query string
        origin = request.args.get('from')
        destination = request.args.get('to')
        start_time = request.args.get('time', '08:00:00')
        # Validate required parameters
        if not origin:
            return jsonify({"error": "Missing 'from' parameter", "success": False}), 400
        if not destination:
            return jsonify({"error": "Missing 'to' parameter", "success": False}), 400
        
        # Get the route
        result = getRoute(origin, destination, start_time)
        
        # Check if there was an error
        if "error" in result:
            return jsonify(result), 404
        
        # Add success flag
        result["success"] = True
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/route', methods=['POST'])
def get_route_api_post():
    """
    Get route between two stations via POST request.
    
    JSON body:
        {
            "from": "CAGLIARI",
            "to": "OLBIA",
            "time": "09:30:00"  // optional
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided", "success": False}), 400
        
        origin = data.get('from')
        destination = data.get('to')
        start_time = data.get('time', '08:00:00')
        
        # Validate required parameters
        if not origin:
            return jsonify({"error": "Missing 'from' field", "success": False}), 400
        if not destination:
            return jsonify({"error": "Missing 'to' field", "success": False}), 400
        
        # Get the route
        result = getRoute(origin, destination, start_time)
        
        # Check if there was an error
        if "error" in result:
            return jsonify(result), 404
        
        # Add success flag
        result["success"] = True
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/stations', methods=['GET'])
def get_stations():
    """
    Get list of all available stations.
    
    Returns:
        {
            "stations": [
                {
                    "stop_id": "830012891",
                    "stop_name": "Stazione di CAGLIARI",
                    "stop_lat": 39.216084,
                    "stop_lon": 9.107992
                },
                ...
            ],
            "success": true
        }
    """
    try:
        stops_path = DATA_DIR_DEFAULT / "stops.csv"
        if not stops_path.exists():
            return jsonify({"error": "Stops data not found", "success": False}), 404
        
        stops = load_stops(stops_path)
        stations = [
            {
                "stop_id": stop.stop_id,
                "stop_name": stop.name,
                "stop_lat": stop.lat,
                "stop_lon": stop.lon
            }
            for stop in stops.values()
        ]
        
        return jsonify({"stations": stations, "success": True})
        
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "train-routing-api", "success": True})

@app.route('/', methods=['GET'])
def home():
    """API documentation."""
    return jsonify({
        "message": "Train Routing API",
        "endpoints": {
            "GET /api/route": "Get route between stations (query params: from, to, time)",
            "POST /api/route": "Get route between stations (JSON body: {from, to, time})",
            "GET /api/stations": "Get list of all stations",
            "GET /api/health": "Health check"
        },
        "examples": {
            "get_route": "/api/route?from=CAGLIARI&to=OLBIA&time=08:00:00",
            "post_route": "POST /api/route with JSON: {\"from\": \"CAGLIARI\", \"to\": \"OLBIA\", \"time\": \"08:00:00\"}"
        }
    })

if __name__ == '__main__':
    print("Starting Train Routing API...")
    print("Available endpoints:")
    print("  GET  /api/route?from=STATION1&to=STATION2&time=HH:MM:SS")
    print("  POST /api/route (JSON body)")
    print("  GET  /api/stations")
    print("  GET  /api/health")
    print("")
    app.run(debug=True, host='0.0.0.0', port=8080)
