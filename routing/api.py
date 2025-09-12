"""
Flask API for train routing service.

Provides REST endpoints to get routes between stations using station IDs.
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
        - from: Origin station ID (e.g., "830012810")
        - to: Destination station ID (e.g., "830012818")
        - time: Optional departure time (HH:MM:SS format, default: "08:00:00")
        - date: Optional departure date (YYYY-MM-DD format, default: today)
    
    Example:
        GET /api/route?from=830012810&to=830012818
        GET /api/route?from=830012810&to=830012818&time=09:30:00
    """
    try:
        # Get parameters from query string
        origin_id = request.args.get('from')
        destination_id = request.args.get('to')
        start_time = request.args.get('time', '08:00:00')
        
        # Validate required parameters
        if not origin_id:
            return jsonify({"error": "Missing 'from' parameter (station ID required)", "success": False}), 400
        if not destination_id:
            return jsonify({"error": "Missing 'to' parameter (station ID required)", "success": False}), 400
        
        # Get the route
        result = getRoute(origin_id, destination_id, start_time)
        
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
    Get list of all available stations with their IDs.
    
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

if __name__ == '__main__':
    print("Starting Train Routing API...")
    print("Available endpoints:")
    print("  GET  /api/route?from=STATION_ID&to=STATION_ID&time=HH:MM:SS")
    print("  GET  /api/stations (list all available stations)")
    print("")
    print("Example:")
    print("  GET /api/route?from=830012810&to=830012818&time=08:00:00")
    print("")
    app.run(debug=True, host='0.0.0.0', port=8080)
