"""
Test script for the Flask routing API.
Run this while the Flask API server is running.
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:5000"

def test_health():
    """Test the health check endpoint."""
    print("=== Testing Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_stations():
    """Test getting all stations."""
    print("=== Testing Get Stations ===")
    try:
        response = requests.get(f"{BASE_URL}/api/stations")
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get("success"):
            print(f"Found {len(data['stations'])} stations")
            # Show first 3 stations
            for station in data['stations'][:3]:
                print(f"  {station['stop_name']} (ID: {station['stop_id']})")
        else:
            print(f"Error: {data.get('error')}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_route_get():
    """Test getting a route via GET request."""
    print("=== Testing Route via GET ===")
    try:
        # Test with station names
        params = {"from": "CAGLIARI", "to": "OLBIA", "time": "08:00:00"}
        response = requests.get(f"{BASE_URL}/api/route", params=params)
        print(f"Status: {response.status_code}")
        data = response.json()
        
        if data.get("success"):
            print(f"Route found: {data['origin_name']} → {data['destination_name']}")
            print(f"Travel time: {data['total_travel_minutes']} minutes")
            print(f"Stops: {data['stop_count']}, Transfers: {data['transfer_count']}")
        else:
            print(f"Error: {data.get('error')}")
            
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_route_post():
    """Test getting a route via POST request."""
    print("=== Testing Route via POST ===")
    try:
        # Test with station names
        payload = {"from": "CAGLIARI", "to": "OLBIA", "time": "09:00:00"}
        response = requests.post(f"{BASE_URL}/api/route", json=payload)
        print(f"Status: {response.status_code}")
        data = response.json()
        
        if data.get("success"):
            print(f"Route found: {data['origin_name']} → {data['destination_name']}")
            print(f"Travel time: {data['total_travel_minutes']} minutes")
            print(f"Stops: {data['stop_count']}, Transfers: {data['transfer_count']}")
        else:
            print(f"Error: {data.get('error')}")
            
    except Exception as e:
        print(f"Error: {e}")
    print()

if __name__ == "__main__":
    print("Testing Flask Routing API")
    print("Make sure the Flask server is running on http://localhost:5000")
    print()
    
    test_health()
    test_stations()
    test_route_get()
    test_route_post()
