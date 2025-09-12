from __future__ import annotations

import json
import math
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import networkx as nx
from loading import (Stop, load_calendar_dates, load_routes_info,
                     load_stop_times_by_trip, load_stops, load_trips_info)

DATA_DIR_DEFAULT = Path("public/data")

def parse_time_to_seconds(t: str) -> Optional[int]:
    if not t or t.lower() == "nan":
        return None
    try:
        dt = datetime.strptime(t.strip(), "%H:%M:%S")
        return dt.hour * 3600 + dt.minute * 60 + dt.second
    except ValueError:
        return None

def seconds_to_time(seconds: int) -> str:
    return str(time(seconds // 3600, (seconds % 3600) // 60, seconds % 60))

def build_transit_graph(
    stops: Dict[str, Stop],
    trips: Dict[str, List[dict]],
    routes: Dict[str, dict],
    trip_routes: Dict[str, dict],
    start_time_secs: int,
    date: str
) -> Tuple[nx.DiGraph, Dict[str, List[Tuple[str, int]]]]:
    """
    Build a time-expanded graph for transit routing.
    
    Returns:
        - NetworkX directed graph
        - Dictionary mapping stop_id to list of (node_id, departure_time) for that stop
    """
    G = nx.DiGraph()
    stop_departures = {}  # stop_id -> [(node_id, departure_time)]
    
    for stop_id in stops:
        stop_departures[stop_id] = []
    
    # Filter trips to only include those running on the specified date
    calendar_dates_path = DATA_DIR_DEFAULT / "calendar_dates.csv"
    service_dates = load_calendar_dates(calendar_dates_path)
    
    # Get service_ids running on the given date
    active_service_ids = {
        service_id for service_id, dates in service_dates.items() if date in dates
    }
    
    # Filter trips by active service_ids
    date_relevant_trips = {
        trip_id: stop_sequence
        for trip_id, stop_sequence in trips.items()
        if trip_routes.get(trip_id, {}).get("service_id") in active_service_ids
    }
    
    # Filter trips to only include those with departures after start_time
    relevant_trips = {}
    for trip_id, stop_sequence in date_relevant_trips.items():
        has_relevant_departure = any(
            parse_time_to_seconds(stop_time.get("departure_time", "")) and
            parse_time_to_seconds(stop_time.get("departure_time", "")) >= start_time_secs
            for stop_time in stop_sequence
        )
        if has_relevant_departure:
            relevant_trips[trip_id] = stop_sequence
    
    print(f"Processing {len(relevant_trips)} relevant trips for date {date} out of {len(trips)} total trips")
    
    # Add nodes and edges for each relevant trip
    for trip_id, stop_sequence in relevant_trips.items():
        trip_info = trip_routes.get(trip_id, {})
        route_id = trip_info.get("route_id", "")
        route_info = routes.get(route_id, {})
        
        prev_node_id = None
        prev_arrival_time = None
        
        for idx, stop_time in enumerate(stop_sequence):
            stop_id = stop_time["stop_id"]
            arrival_secs = parse_time_to_seconds(stop_time.get("arrival_time", ""))
            departure_secs = parse_time_to_seconds(stop_time.get("departure_time", ""))
            
            if arrival_secs is None or departure_secs is None:
                continue
                
            # Only consider stops within a reasonable time window (e.g., 24 hours)
            # to prevent the graph from becoming too large
            if departure_secs > start_time_secs + 24 * 3600:  # Skip if more than 24 hours later
                continue
            
            # Create unique node ID for this stop on this trip
            node_id = f"{stop_id}_{trip_id}_{idx}"
            
            # Add node with attributes
            G.add_node(node_id, 
                      stop_id=stop_id,
                      trip_id=trip_id,
                      route_id=route_id,
                      arrival_time=arrival_secs,
                      departure_time=departure_secs,
                      stop_sequence=idx,
                      stop_name=stops.get(stop_id, Stop("", "", 0, 0)).name,
                      route_name=route_info.get("route_short_name", route_id),
                      route_description=route_info.get("route_long_name", ""),
                      trip_headsign=trip_info.get("trip_headsign", ""),
                      trip_short_name=trip_info.get("trip_short_name", ""),
                      date=date)
            
            # Track departures from this stop
            stop_departures[stop_id].append((node_id, departure_secs))
            
            # Add edge from previous stop on the same trip (in-vehicle travel)
            if prev_node_id is not None and prev_arrival_time is not None:
                travel_time = arrival_secs - prev_arrival_time
                if travel_time >= 0:  # Allow zero-minute travel time
                    G.add_edge(prev_node_id, node_id, 
                              weight=travel_time,
                              edge_type="in_vehicle",
                              trip_id=trip_id)
            
            prev_node_id = node_id
            prev_arrival_time = departure_secs
    
    # Add transfer edges between different trips at the same stop (optimized)
    transfer_penalty = 600  # 1 minute penalty for each transfer
    for stop_id, departures in stop_departures.items():
        # Sort departures by time
        departures.sort(key=lambda x: x[1])
        
        # Limit transfers: only connect to the next few departures to avoid exponential edges
        MAX_TRANSFERS_PER_ARRIVAL = 2 
        
        for i, (from_node, from_time) in enumerate(departures):
            from_trip = G.nodes[from_node]["trip_id"]
            from_arrival = G.nodes[from_node]["arrival_time"]
            transfers_added = 0
            
            # Connect to next few departures from the same stop (transfers)
            for j in range(i + 1, min(i + 1 + MAX_TRANSFERS_PER_ARRIVAL, len(departures))):
                to_node, to_time = departures[j]
                to_trip = G.nodes[to_node]["trip_id"]
                
                # Only add transfer edge if different trips
                if from_trip != to_trip:
                    # The weight should be the waiting time plus the penalty
                    wait_time = to_time - from_arrival
                    if wait_time >= 0:
                        G.add_edge(from_node, to_node,
                                  weight=wait_time + transfer_penalty,
                                  edge_type="transfer",
                                  transfer_stop=stop_id)
                        transfers_added += 1
                        
                        if transfers_added >= 2:  # Max 2 transfer options
                            break
    
    print(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G, stop_departures


def find_earliest_arrival_path(
    G: nx.DiGraph,
    stop_departures: Dict[str, List[Tuple[str, int]]],
    origin_id: str,
    dest_id: str,
    start_time_secs: int
) -> Optional[List[str]]:
    """
    Find the earliest arrival path using NetworkX shortest path.
    """
    # Find all possible starting nodes (departures from origin after start_time)
    origin_departures = stop_departures.get(origin_id, [])
    valid_starts = [node_id for node_id, dep_time in origin_departures 
                   if dep_time >= start_time_secs]
    
    print(f"Found {len(valid_starts)} valid starting nodes from {origin_id}")
    
    if not valid_starts:
        return None
    
    # Find all destination nodes
    dest_departures = stop_departures.get(dest_id, [])
    dest_nodes = [node_id for node_id, _ in dest_departures]
    
    print(f"Found {len(dest_nodes)} destination nodes at {dest_id}")
    
    if not dest_nodes:
        return None
    
    # Find shortest path from any valid start to any destination
    best_path = None
    best_arrival_time = math.inf
    
    # Limit the search to avoid timeout - try only first few starting points
    max_starts_to_try = min(10, len(valid_starts))
    
    for i, start_node in enumerate(valid_starts[:max_starts_to_try]):
        if i > 0 and i % 5 == 0:
            print(f"Tried {i} starting nodes...")
            
        # Use multi-target Dijkstra to find shortest paths to all possible destinations
        try:
            lengths, paths = nx.single_source_dijkstra(G, start_node, weight='weight')
            
            for dest_node in dest_nodes:
                if dest_node in lengths:
                    arrival_time = G.nodes[dest_node]["arrival_time"]
                    if arrival_time < best_arrival_time:
                        best_arrival_time = arrival_time
                        best_path = paths[dest_node]
        except nx.NetworkXNoPath:
            continue
    
    return best_path


def path_to_detailed_route(
    G: nx.DiGraph,
    path: List[str],
    stops: Dict[str, Stop],
    origin_id: str,
    dest_id: str,
    start_time: str,
    date: str
) -> dict:
    """
    Convert NetworkX path to the detailed route format expected by the API,
    and clean up redundant transfers.
    """
    if not path:
        return {"error": "No path found"}

    # Handle transfer at the origin: if the first action is a transfer, start the route from the second node.
    if len(path) > 1:
        first_node = G.nodes[path[0]]
        second_node = G.nodes[path[1]]
        if first_node["stop_id"] == second_node["stop_id"] and first_node["trip_id"] != second_node["trip_id"]:
            path = path[1:]

    # Path cleanup to remove redundant transfers
    if len(path) > 1:
        cleaned_path = [path[0]]
        i = 1
        while i < len(path):
            current_node_id = path[i]
            prev_node_id = cleaned_path[-1]
            
            current_stop_id = G.nodes[current_node_id]["stop_id"]
            prev_stop_id = G.nodes[prev_node_id]["stop_id"]
            
            # Check for self-transfer (transfer at same stop to a new trip)
            if current_stop_id == prev_stop_id:
                # Look ahead to see if the next stop is also the same, which means we are just waiting
                if i + 1 < len(path):
                    next_node_id = path[i+1]
                    next_stop_id = G.nodes[next_node_id]["stop_id"]
                    if next_stop_id == current_stop_id:
                        # This is a redundant transfer, skip to the next node
                        i += 1
                        continue
            
            cleaned_path.append(current_node_id)
            i += 1
        path = cleaned_path

    processed_stops = []
    transfers = []
    last_trip_id = None
    
    for i, node_id in enumerate(path):
        node_data = G.nodes[node_id]
        stop_id = node_data["stop_id"]
        trip_id = node_data["trip_id"]
        route_id = node_data["route_id"]
        
        # Get stop coordinates
        stop_obj = stops.get(stop_id)
        stop_lat = stop_obj.lat if stop_obj else 0.0
        stop_lon = stop_obj.lon if stop_obj else 0.0
        
        # Convert times back to string format
        arrival_time = seconds_to_time(node_data["arrival_time"])
        departure_time = seconds_to_time(node_data["departure_time"])
        
        # Check for transfers
        is_transfer = False
        transfer_note = ""
        
        if i > 0 and last_trip_id is not None and trip_id != last_trip_id:
            is_transfer = True
            transfer_note = f"Transfer from trip {last_trip_id} to trip {trip_id}"
            transfers.append({
                "at_stop": node_data["stop_name"],
                "stop_id": stop_id,
                "stop_lat": stop_lat,
                "stop_lon": stop_lon,
                "transfer_info": transfer_note,
                "from_trip": last_trip_id,
                "to_trip": trip_id,
                "from_route": G.nodes[path[i-1]]["route_id"] if i > 0 else "",
                "to_route": route_id
            })
        
        # Add stop to detailed route
        stop_info = {
            "stop_id": stop_id,
            "stop_name": node_data["stop_name"],
            "stop_lat": stop_lat,
            "stop_lon": stop_lon,
            "arrival_time": arrival_time,
            "departure_time": departure_time,
            "trip_id": trip_id,
            "route_id": route_id,
            "route_name": node_data["route_name"],
            "route_description": node_data["route_description"],
            "trip_headsign": node_data.get("trip_headsign", ""),
            "trip_short_name": node_data.get("trip_short_name", ""),
            "date": node_data.get("date", date),
            "is_transfer": is_transfer
        }
        
        if is_transfer:
            stop_info["transfer_note"] = transfer_note
            stop_info["transfer_type"] = "departure"
        
        processed_stops.append(stop_info)
        last_trip_id = trip_id
    
    # Calculate total travel time
    start_secs = G.nodes[path[0]]["departure_time"]
    final_arrival_secs = G.nodes[path[-1]]["arrival_time"]
    
    # The path weight from Dijkstra includes penalties, so we calculate travel time from start/end times
    total_travel_minutes = round((final_arrival_secs - start_secs) / 60, 1) if start_secs else 0
    
    return {
        "origin": origin_id,
        "origin_name": stops[origin_id].name if origin_id in stops else origin_id,
        "destination": dest_id,
        "destination_name": stops[dest_id].name if dest_id in stops else dest_id,
        "start_time": start_time,
        "date": date,
        "arrival_time": seconds_to_time(final_arrival_secs),
        "total_travel_minutes": total_travel_minutes,
        "stop_count": len(processed_stops),
        "transfer_count": len(transfers),
        "transfers": transfers,
        "detailed_route": processed_stops
    }


def earliest_arrival_routing(
    stops: Dict[str, Stop],
    trips: Dict[str, List[dict]],
    routes: Dict[str, dict],
    trip_routes: Dict[str, dict],
    origin_id: str,
    dest_id: str,
    start_time: str,
    date: str
) -> dict:
    """
    Returns detailed route with all stops and transfer information using NetworkX.
    """
    start_secs = parse_time_to_seconds(start_time)
    date = date.replace("-", "")
    if start_secs is None:
        return {"error": f"Invalid start_time: {start_time}"}
    
    # Build the transit graph
    G, stop_departures = build_transit_graph(stops, trips, routes, trip_routes, start_secs, date)
    
    # Find the shortest path
    path = find_earliest_arrival_path(G, stop_departures, origin_id, dest_id, start_secs)
    
    if path is None:
        return {"error": f"No route found from {origin_id} to {dest_id} after {start_time} on {date}"}
    
    # Convert path to detailed route format
    return path_to_detailed_route(G, path, stops, origin_id, dest_id, start_time, date)

def compute_route(origin_id: str, dest_id: str, start_time: str, date: str, data_dir: Path = DATA_DIR_DEFAULT):
    stops_path = data_dir / "stops.csv"
    stop_times_path = data_dir / "stop_times.csv"
    routes_path = data_dir / "routes.csv"
    trips_path = data_dir / "trips.csv"
    
    stops = load_stops(stops_path)
    trips = load_stop_times_by_trip(stop_times_path)
    routes = load_routes_info(routes_path)
    trip_routes = load_trips_info(trips_path)
    
    if origin_id is None:
        raise ValueError(f"Origin stop not found: {origin_id}")
    if dest_id is None:
        raise ValueError(f"Destination stop not found: {dest_id}")
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
    return earliest_arrival_routing(stops, trips, routes, trip_routes, origin_id, dest_id, start_time, date)

def getRoute(station1: str, station2: str, start_time: str = "08:00:00", date: str = "20241215", data_dir: Path = DATA_DIR_DEFAULT) -> dict:
    try:
        return compute_route(station1, station2, start_time, date, data_dir)
    except Exception as e:
        return {"error": str(e), "success": False}

# --- Editable variables for quick testing ---
origin = "830012810"      # stop id or (partial) name
destination = "830012819"    # stop id or (partial) name
start_time = "08:00:00"  # departure time from origin (HH:MM:SS)
date = "20241215"        # YYYYMMDD format
data_dir = DATA_DIR_DEFAULT  # Path to GTFS CSVs
pretty = True  # Pretty-print JSON output

if __name__ == "__main__":
    # Example API usage:
    # route = getRoute("CAGLIARI", "OLBIA", "09:30:00", "20230520")
    
    try:
        result = getRoute(origin, destination, start_time, date, data_dir)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        raise SystemExit(1)
    if pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))
