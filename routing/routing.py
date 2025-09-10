"""
Enhanced routing script: finds the optimal route between two stations with detailed stop information and route transfer detection.

Features:
- Time-dependent routing respecting train schedules
- Detailed information for each stop (stop_id, stop_name, arrival, departure)
- Route transfer detection and notification
- Complete journey with all intermediate stops
- Trip information for each segment

Usage: set origin, destination, and start_time variables below, then run the script.
"""

from __future__ import annotations
import csv, json, math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

DATA_DIR_DEFAULT = Path("public/data")

def parse_time_to_seconds(t: str) -> Optional[int]:
    """Parse GTFS HH:MM:SS time (may exceed 24h) to seconds; return None if invalid."""
    if not t or t.lower() == "nan":
        return None
    try:
        parts = t.strip().split(":")
        if len(parts) != 3:
            return None
        h, m, s = map(int, parts)
        return h * 3600 + m * 60 + s
    except Exception:
        return None

def seconds_to_time(seconds: int) -> str:
    """Convert seconds to HH:MM:SS format."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

@dataclass
class Stop:
    stop_id: str
    name: str
    lat: float
    lon: float

def load_stops(stops_path: Path) -> Dict[str, Stop]:
    stops: Dict[str, Stop] = {}
    with stops_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("stop_id"):
                continue
            try:
                stops[row["stop_id"]] = Stop(
                    stop_id=row["stop_id"],
                    name=row.get("stop_name", ""),
                    lat=float(row.get("stop_lat") or 0.0),
                    lon=float(row.get("stop_lon") or 0.0),
                )
            except ValueError:
                continue
    return stops

def load_stop_times_by_trip(stop_times_path: Path) -> Dict[str, List[dict]]:
    """Return dict: trip_id -> ordered list of stop_times rows."""
    trips = defaultdict(list)
    with stop_times_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trips[row["trip_id"]].append(row)
    # Sort each trip by stop_sequence
    for trip_id in trips:
        trips[trip_id].sort(key=lambda r: int(r.get("stop_sequence", 0)))
    return trips

def load_routes_info(routes_path: Path) -> Dict[str, dict]:
    """Load route information for transfer detection."""
    routes = {}
    try:
        with routes_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                routes[row.get("route_id", "")] = {
                    "route_short_name": row.get("route_short_name", ""),
                    "route_long_name": row.get("route_long_name", ""),
                    "route_type": row.get("route_type", "")
                }
    except FileNotFoundError:
        pass
    return routes

def load_trips_info(trips_path: Path) -> Dict[str, dict]:
    """Load trip to route mapping."""
    trip_routes = {}
    try:
        with trips_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                trip_routes[row.get("trip_id", "")] = {
                    "route_id": row.get("route_id", ""),
                    "trip_headsign": row.get("trip_headsign", "")
                }
    except FileNotFoundError:
        pass
    return trip_routes

def fuzzy_find_stop_id(stops: Dict[str, Stop], query: str) -> Optional[str]:
    q = query.strip().lower()
    if q in stops:  # direct id match
        return q
    for sid, st in stops.items():
        if st.name.lower() == q:
            return sid
    candidates = [sid for sid, st in stops.items() if q in st.name.lower()]
    if candidates:
        candidates.sort()
        return candidates[0]
    if query.isdigit() and query in stops:
        return query
    return None

def earliest_arrival_routing(
    stops: Dict[str, Stop],
    trips: Dict[str, List[dict]],
    routes: Dict[str, dict],
    trip_routes: Dict[str, dict],
    origin_id: str,
    dest_id: str,
    start_time: str
) -> dict:
    """
    Returns detailed route with all stops and transfer information.
    """
    start_secs = parse_time_to_seconds(start_time)
    if start_secs is None:
        return {"error": f"Invalid start_time: {start_time}"}

    # Build a list of all departures from origin after start_time
    departures = []  # (dep_secs, trip_id, stop_idx)
    for trip_id, stop_seq in trips.items():
        for idx, row in enumerate(stop_seq):
            if row["stop_id"] == origin_id:
                dep_secs = parse_time_to_seconds(row.get("departure_time", ""))
                if dep_secs is not None and dep_secs >= start_secs:
                    departures.append((dep_secs, trip_id, idx))

    if not departures:
        return {"error": f"No departures from {origin_id} after {start_time}"}

    # Earliest arrival Dijkstra with path reconstruction
    import heapq
    visited = dict()  # (stop_id, trip_id, stop_idx): (earliest_arrival, path_info)
    pq = []
    counter = 0
    
    for dep_secs, trip_id, idx in departures:
        initial_stop_info = {
            "stop_id": origin_id,
            "stop_name": stops[origin_id].name if origin_id in stops else origin_id,
            "trip_id": trip_id,
            "route_id": trip_routes.get(trip_id, {}).get("route_id", ""),
            "arrival_time": trips[trip_id][idx].get("arrival_time"),
            "departure_time": trips[trip_id][idx].get("departure_time"),
            "is_transfer": False
        }
        heapq.heappush(pq, (dep_secs, counter, origin_id, trip_id, idx, [initial_stop_info]))
        counter += 1

    best_arrival = math.inf
    best_path = None

    while pq:
        arr_secs, _, stop_id, trip_id, idx, path = heapq.heappop(pq)
        key = (stop_id, trip_id, idx)
        if key in visited and visited[key][0] <= arr_secs:
            continue
        visited[key] = (arr_secs, path)

        if stop_id == dest_id:
            if arr_secs < best_arrival:
                best_arrival = arr_secs
                best_path = path
            continue

        # Continue on same trip if possible
        if idx + 1 < len(trips[trip_id]):
            next_row = trips[trip_id][idx + 1]
            next_stop_id = next_row["stop_id"]
            next_arr_secs = parse_time_to_seconds(next_row.get("arrival_time", ""))
            if next_arr_secs is not None and next_arr_secs >= arr_secs:
                next_stop_info = {
                    "stop_id": next_stop_id,
                    "stop_name": stops[next_stop_id].name if next_stop_id in stops else next_stop_id,
                    "trip_id": trip_id,
                    "route_id": trip_routes.get(trip_id, {}).get("route_id", ""),
                    "arrival_time": next_row.get("arrival_time"),
                    "departure_time": next_row.get("departure_time"),
                    "is_transfer": False
                }
                new_path = path + [next_stop_info]
                heapq.heappush(pq, (next_arr_secs, counter, next_stop_id, trip_id, idx + 1, new_path))
                counter += 1

        # Allow transfers: for all trips departing from current stop after current time
        for t_id, stop_seq in trips.items():
            if t_id == trip_id:  # Skip same trip
                continue
            for i, row in enumerate(stop_seq):
                if row["stop_id"] == stop_id:
                    dep_secs = parse_time_to_seconds(row.get("departure_time", ""))
                    if dep_secs is not None and dep_secs > arr_secs:
                        transfer_route_id = trip_routes.get(t_id, {}).get("route_id", "")
                        transfer_stop_info = {
                            "stop_id": stop_id,
                            "stop_name": stops[stop_id].name if stop_id in stops else stop_id,
                            "trip_id": t_id,
                            "route_id": transfer_route_id,
                            "arrival_time": row.get("arrival_time"),
                            "departure_time": row.get("departure_time"),
                            "is_transfer": True,
                        }
                        heapq.heappush(pq, (dep_secs, counter, stop_id, t_id, i, path))
                        counter += 1

    if best_path is None:
        return {"error": f"No route found from {origin_id} to {dest_id} after {start_time}"}

    # Process the path to add route information and detect transfers
    processed_stops = []
    transfers = []
    last_trip_id = None
    
    for i, stop_info in enumerate(best_path):
        route_id = stop_info.get("route_id", "")
        route_info = routes.get(route_id, {})
        trip_id = stop_info.get("trip_id", "")
        
        # Detect transfer: when trip_id changes
        is_transfer = False
        transfer_note = ""
        
        if i > 0 and last_trip_id is not None and trip_id != last_trip_id:
            is_transfer = True
            last_route_id = trip_routes.get(last_trip_id, {}).get("route_id", "")
            current_route_id = trip_routes.get(trip_id, {}).get("route_id", "")
            transfer_note = f"Transfer from trip {last_trip_id} (route {last_route_id}) to trip {trip_id} (route {current_route_id})"
            transfers.append({
                "at_stop": stop_info["stop_name"],
                "stop_id": stop_info["stop_id"],
                "transfer_info": transfer_note,
                "from_trip": last_trip_id,
                "to_trip": trip_id,
                "from_route": last_route_id,
                "to_route": current_route_id
            })
        
        enhanced_stop = {
            "stop_id": stop_info["stop_id"],
            "stop_name": stop_info["stop_name"],
            "arrival_time": stop_info["arrival_time"],
            "departure_time": stop_info["departure_time"],
            "trip_id": stop_info["trip_id"],
            "route_id": route_id,
            "route_name": route_info.get("route_short_name", route_id),
            "route_description": route_info.get("route_long_name", ""),
            "is_transfer": is_transfer
        }
        
        if is_transfer:
            enhanced_stop["transfer_note"] = transfer_note
        
        processed_stops.append(enhanced_stop)
        last_trip_id = trip_id

    return {
        "origin": origin_id,
        "origin_name": stops[origin_id].name if origin_id in stops else origin_id,
        "destination": dest_id,
        "destination_name": stops[dest_id].name if dest_id in stops else dest_id,
        "start_time": start_time,
        "arrival_time": seconds_to_time(best_arrival),
        "total_travel_minutes": round((best_arrival - start_secs) / 60, 1),
        "stop_count": len(processed_stops),
        "transfer_count": len(transfers),
        "transfers": transfers,
        "detailed_route": processed_stops
    }
def compute_route(origin_query: str, destination_query: str, start_time: str, data_dir: Path = DATA_DIR_DEFAULT):
    stops_path = data_dir / "stops.csv"
    stop_times_path = data_dir / "stop_times.csv"
    routes_path = data_dir / "routes.csv"
    trips_path = data_dir / "trips.csv"
    
    if not stops_path.exists() or not stop_times_path.exists():
        raise FileNotFoundError(f"Expected GTFS files in {data_dir}")
    
    stops = load_stops(stops_path)
    trips = load_stop_times_by_trip(stop_times_path)
    routes = load_routes_info(routes_path)
    trip_routes = load_trips_info(trips_path)
    
    origin_id = fuzzy_find_stop_id(stops, origin_query)
    dest_id = fuzzy_find_stop_id(stops, destination_query)
    
    if origin_id is None:
        raise ValueError(f"Origin stop not found: {origin_query}")
    if dest_id is None:
        raise ValueError(f"Destination stop not found: {destination_query}")
    if origin_id == dest_id:
        return {
            "origin": origin_id,
            "destination": dest_id,
            "start_time": start_time,
            "total_travel_minutes": 0,
            "detailed_route": [{
                "stop_id": origin_id,
                "stop_name": stops[origin_id].name,
                "arrival_time": start_time,
                "departure_time": start_time,
                "note": "Origin equals destination"
            }],
            "note": "Origin equals destination",
        }
    
    return earliest_arrival_routing(stops, trips, routes, trip_routes, origin_id, dest_id, start_time)

def getRoute(station1: str, station2: str, start_time: str = "08:00:00", data_dir: Path = DATA_DIR_DEFAULT) -> dict:
    """
    API function to get route between two stations.
    
    Args:
        station1: Origin station (stop_id or partial station name)
        station2: Destination station (stop_id or partial station name) 
        start_time: Departure time from origin (HH:MM:SS format, default: "08:00:00")
        data_dir: Directory containing GTFS CSV files (default: "public/data")
    
    Returns:
        dict: Route information including:
            - origin/destination details
            - total_travel_minutes
            - detailed_route: list of all stops with arrival/departure times
            - transfers: list of route transfers
            - stop_count, transfer_count
    
    Example:
        route = getRoute("CAGLIARI", "OLBIA")
        route = getRoute("830012891", "830012855", "09:30:00")
    """
    try:
        return compute_route(station1, station2, start_time, data_dir)
    except Exception as e:
        return {"error": str(e), "success": False}

# --- Editable variables for quick testing ---
origin = "CAGLIARI"      # stop id or (partial) name
destination = "OLBIA"    # stop id or (partial) name
start_time = "08:00:00"  # departure time from origin (HH:MM:SS)
data_dir = DATA_DIR_DEFAULT  # Path to GTFS CSVs
pretty = True  # Pretty-print JSON output

if __name__ == "__main__":
    # Example API usage:
    # route = getRoute("CAGLIARI", "OLBIA")
    # route = getRoute("CAGLIARI", "OLBIA", "09:30:00")
    
    try:
        result = getRoute(origin, destination, start_time, data_dir)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        raise SystemExit(1)
    if pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))
