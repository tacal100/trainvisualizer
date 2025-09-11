"""
GTFS to PDDL converter for temporal train journey planning with transfer support.

Converts GTFS data (stops, routes, trips, stop_times) into PDDL domain 
and problem files that can be solved with temporal planners like OPTIC.
Handles transfers between different trips at common stops.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class TripConnection:
    """Represents a connection within a single trip between consecutive stops."""
    trip_id: str
    route_id: str
    from_stop: str
    to_stop: str
    departure_time: str  # HH:MM:SS format
    arrival_time: str    # HH:MM:SS format
    duration: int        # travel time in minutes
    from_sequence: int   # stop sequence number
    to_sequence: int     # stop sequence number

@dataclass
class Transfer:
    """Represents a possible transfer between two trips at a stop."""
    stop_id: str
    from_trip: str
    to_trip: str
    from_route: str
    to_route: str
    arrival_time: str    # When you arrive on from_trip
    departure_time: str  # When you depart on to_trip
    transfer_time: int   # Minutes needed for transfer

def parse_time_to_minutes(time_str: str) -> int:
    """Convert HH:MM:SS to minutes since midnight."""
    if not time_str or time_str.strip() == "":
        return 0
    
    parts = time_str.strip().split(':')
    if len(parts) != 3:
        return 0
    
    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        
        # Handle times after midnight (24:00:00+)
        if hours >= 24:
            hours = hours % 24
        
        return hours * 60 + minutes + (seconds // 60)
    except ValueError:
        return 0

def minutes_to_time_str(minutes: int) -> str:
    """Convert minutes since midnight back to HH:MM format."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def load_gtfs_data(data_dir: Path) -> Tuple[Dict, Dict, Dict, Dict]:
    """Load all necessary GTFS data."""
    print("Loading GTFS data...")
    
    # Load stops
    stops = {}
    with open(data_dir / "stops.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stops[row['stop_id']] = row
    
    # Load routes
    routes = {}
    with open(data_dir / "routes.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            routes[row['route_id']] = row
    
    # Load trips
    trips = {}
    with open(data_dir / "trips.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trips[row['trip_id']] = row
    
    # Load stop times organized by trip
    stop_times_by_trip = defaultdict(list)
    with open(data_dir / "stop_times.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stop_times_by_trip[row['trip_id']].append(row)
    
    # Sort stop times by sequence
    for trip_id in stop_times_by_trip:
        stop_times_by_trip[trip_id].sort(key=lambda x: int(x.get('stop_sequence', 0)))
    
    print(f"Loaded {len(stops)} stops, {len(routes)} routes, {len(trips)} trips")
    
    return stops, routes, trips, dict(stop_times_by_trip)

def extract_trip_connections(stops: Dict, routes: Dict, trips: Dict, stop_times_by_trip: Dict) -> List[TripConnection]:
    """Extract all connections within trips."""
    connections = []
    
    for trip_id, stop_times in stop_times_by_trip.items():
        trip_info = trips.get(trip_id, {})
        route_id = trip_info.get('route_id', 'unknown')
        
        # Create connections between consecutive stops in this trip
        for i in range(len(stop_times) - 1):
            current_stop = stop_times[i]
            next_stop = stop_times[i + 1]
            
            dep_time = current_stop.get("departure_time", "")
            arr_time = next_stop.get("arrival_time", "")
            
            if dep_time and arr_time:
                dep_minutes = parse_time_to_minutes(dep_time)
                arr_minutes = parse_time_to_minutes(arr_time)
                duration = arr_minutes - dep_minutes
                
                # Skip invalid durations
                if duration <= 0:
                    continue
                
                connections.append(TripConnection(
                    trip_id=trip_id,
                    route_id=route_id,
                    from_stop=current_stop["stop_id"],
                    to_stop=next_stop["stop_id"],
                    departure_time=dep_time,
                    arrival_time=arr_time,
                    duration=duration,
                    from_sequence=int(current_stop.get("stop_sequence", 0)),
                    to_sequence=int(next_stop.get("stop_sequence", 0))
                ))
    
    print(f"Extracted {len(connections)} trip connections")
    return connections

def extract_transfers(stops: Dict, trips: Dict, stop_times_by_trip: Dict, min_transfer_time: int = 5) -> List[Transfer]:
    """Extract possible transfers between different trips at common stops."""
    transfers = []
    
    # Group arrivals and departures by stop
    arrivals_by_stop = defaultdict(list)  # stop_id -> [(trip_id, route_id, arrival_time)]
    departures_by_stop = defaultdict(list)  # stop_id -> [(trip_id, route_id, departure_time)]
    
    for trip_id, stop_times in stop_times_by_trip.items():
        trip_info = trips.get(trip_id, {})
        route_id = trip_info.get('route_id', 'unknown')
        
        for stop_time in stop_times:
            stop_id = stop_time['stop_id']
            arr_time = stop_time.get('arrival_time', '')
            dep_time = stop_time.get('departure_time', '')
            
            if arr_time:
                arrivals_by_stop[stop_id].append((trip_id, route_id, arr_time))
            if dep_time:
                departures_by_stop[stop_id].append((trip_id, route_id, dep_time))
    
    # Find valid transfers at each stop
    for stop_id in stops.keys():
        arrivals = arrivals_by_stop.get(stop_id, [])
        departures = departures_by_stop.get(stop_id, [])
        
        for from_trip, from_route, arr_time in arrivals:
            for to_trip, to_route, dep_time in departures:
                # Skip same trip
                if from_trip == to_trip:
                    continue
                
                arr_minutes = parse_time_to_minutes(arr_time)
                dep_minutes = parse_time_to_minutes(dep_time)
                transfer_time = dep_minutes - arr_minutes
                
                # Valid transfer: enough time but not too long
                if min_transfer_time <= transfer_time <= 120:  # Max 2 hours wait
                    transfers.append(Transfer(
                        stop_id=stop_id,
                        from_trip=from_trip,
                        to_trip=to_trip,
                        from_route=from_route,
                        to_route=to_route,
                        arrival_time=arr_time,
                        departure_time=dep_time,
                        transfer_time=transfer_time
                    ))
    
    print(f"Found {len(transfers)} possible transfers")
    return transfers

def generate_pddl_domain(output_path: Path) -> None:
    """Generate PDDL domain file for train journey planning with transfers."""
    
    domain_content = """(define (domain train-journey-with-transfers)
    (:requirements :strips :typing :durative-actions :timed-initial-literals)
    
    (:types
        stop - object
        trip - object
        route - object
        connection - object
        transfer - object
    )
    
    (:predicates
        ;; Static predicates
        (connection-trip ?conn - connection ?trip - trip)
        (connection-route ?conn - connection ?route - route)
        (connection-from ?conn - connection ?stop - stop)
        (connection-to ?conn - connection ?stop - stop)
        (connection-available ?conn - connection)
        
        (transfer-stop ?trans - transfer ?stop - stop)
        (transfer-from-trip ?trans - transfer ?trip - trip)
        (transfer-to-trip ?trans - transfer ?trip - trip)
        (transfer-available ?trans - transfer)
        
        ;; Dynamic predicates
        (passenger-at ?stop - stop)
        (passenger-on-trip ?trip - trip)
        (current-trip ?trip - trip)
        (journey-completed)
    )
    
    ;; Take a connection within a trip
    (:durative-action take-connection
        :parameters (?conn - connection ?trip - trip ?route - route ?from ?to - stop)
        :duration (= ?duration 1)  ; Will be set by problem-specific instances
        :condition (and
            (at start (passenger-at ?from))
            (at start (connection-trip ?conn ?trip))
            (at start (connection-route ?conn ?route))
            (at start (connection-from ?conn ?from))
            (at start (connection-to ?conn ?to))
            (at start (connection-available ?conn))
        )
        :effect (and
            (at start (not (passenger-at ?from)))
            (at start (passenger-on-trip ?trip))
            (at start (current-trip ?trip))
            (at start (not (connection-available ?conn)))
            (at end (not (passenger-on-trip ?trip)))
            (at end (passenger-at ?to))
        )
    )
    
    ;; Make a transfer between trips
    (:durative-action make-transfer
        :parameters (?trans - transfer ?stop - stop ?from-trip ?to-trip - trip)
        :duration (= ?duration 1)  ; Will be set by problem-specific instances
        :condition (and
            (at start (passenger-at ?stop))
            (at start (transfer-stop ?trans ?stop))
            (at start (transfer-from-trip ?trans ?from-trip))
            (at start (transfer-to-trip ?trans ?to-trip))
            (at start (transfer-available ?trans))
        )
        :effect (and
            (at start (not (transfer-available ?trans)))
            (at start (current-trip ?to-trip))
            (at end (passenger-at ?stop))  ; Still at same stop after transfer
        )
    )
    
    ;; Wait at a stop
    (:durative-action wait-at-stop
        :parameters (?stop - stop)
        :duration (= ?duration 1)
        :condition (at start (passenger-at ?stop))
        :effect (and)
    )
)"""
    
    with open(output_path, 'w') as f:
        f.write(domain_content)

def generate_pddl_problem(
    connections: List[TripConnection],
    transfers: List[Transfer],
    origin_stop: str,
    destination_stop: str,
    start_time: str,
    stops: Dict,
    routes: Dict,
    trips: Dict,
    output_path: Path
) -> None:
    """Generate PDDL problem file for a specific journey with transfers."""
    
    start_minutes = parse_time_to_minutes(start_time)
    
    # Extract unique objects
    all_stops = set([origin_stop, destination_stop])
    all_trips = set()
    all_routes = set()
    
    for conn in connections:
        all_stops.add(conn.from_stop)
        all_stops.add(conn.to_stop)
        all_trips.add(conn.trip_id)
        all_routes.add(conn.route_id)
    
    for trans in transfers:
        all_stops.add(trans.stop_id)
        all_trips.add(trans.from_trip)
        all_trips.add(trans.to_trip)
        all_routes.add(trans.from_route)
        all_routes.add(trans.to_route)
    
    # Filter relevant connections (after start time)
    relevant_connections = []
    for i, conn in enumerate(connections):
        dep_minutes = parse_time_to_minutes(conn.departure_time)
        if dep_minutes >= start_minutes:
            relevant_connections.append((conn, f"conn-{i}"))
    
    # Filter relevant transfers
    relevant_transfers = []
    for i, trans in enumerate(transfers):
        dep_minutes = parse_time_to_minutes(trans.departure_time)
        if dep_minutes >= start_minutes:
            relevant_transfers.append((trans, f"trans-{i}"))
    
    problem_content = f"""(define (problem train-journey-problem)
    (:domain train-journey-with-transfers)
    
    (:objects
        ;; Stops
        {' '.join(f'stop-{stop}' for stop in sorted(all_stops))} - stop
        
        ;; Trips
        {' '.join(f'trip-{trip.replace("-", "_")}' for trip in sorted(all_trips))} - trip
        
        ;; Routes
        {' '.join(f'route-{route}' for route in sorted(all_routes))} - route
        
        ;; Connections
        {' '.join(conn_id for _, conn_id in relevant_connections)} - connection
        
        ;; Transfers
        {' '.join(trans_id for _, trans_id in relevant_transfers)} - transfer
    )
    
    (:init
        ;; Initial passenger location
        (passenger-at stop-{origin_stop})
        
        ;; Connection definitions
"""
    
    # Add connection definitions and timed availability
    for conn, conn_id in relevant_connections:
        trip_clean = conn.trip_id.replace("-", "_")
        problem_content += f"        (connection-trip {conn_id} trip-{trip_clean})\n"
        problem_content += f"        (connection-route {conn_id} route-{conn.route_id})\n"
        problem_content += f"        (connection-from {conn_id} stop-{conn.from_stop})\n"
        problem_content += f"        (connection-to {conn_id} stop-{conn.to_stop})\n"
        
        # Make connection available at departure time
        dep_minutes = parse_time_to_minutes(conn.departure_time)
        relative_time = dep_minutes - start_minutes
        
        if relative_time >= 0:
            problem_content += f"        (at {relative_time} (connection-available {conn_id}))\n"
            # Connection window closes after departure
            problem_content += f"        (at {relative_time + 1} (not (connection-available {conn_id})))\n"
    
    problem_content += "\n        ;; Transfer definitions\n"
    
    # Add transfer definitions and timed availability
    for trans, trans_id in relevant_transfers:
        from_trip_clean = trans.from_trip.replace("-", "_")
        to_trip_clean = trans.to_trip.replace("-", "_")
        problem_content += f"        (transfer-stop {trans_id} stop-{trans.stop_id})\n"
        problem_content += f"        (transfer-from-trip {trans_id} trip-{from_trip_clean})\n"
        problem_content += f"        (transfer-to-trip {trans_id} trip-{to_trip_clean})\n"
        
        # Transfer available when the connecting trip departs
        dep_minutes = parse_time_to_minutes(trans.departure_time)
        relative_time = dep_minutes - start_minutes
        
        if relative_time >= 0:
            problem_content += f"        (at {relative_time} (transfer-available {trans_id}))\n"
            problem_content += f"        (at {relative_time + 1} (not (transfer-available {trans_id})))\n"
    
    problem_content += f"""
    )
    
    (:goal
        (passenger-at stop-{destination_stop})
    )
    
    ;; Minimize total time
    (:metric minimize (total-time))
)"""
    
    # Now add durative action instances with specific durations
    durative_actions = "\n;; Durative action instances\n"
    
    for conn, conn_id in relevant_connections:
        trip_clean = conn.trip_id.replace("-", "_")
        durative_actions += f"""
(:durative-action take-{conn_id}
    :parameters ()
    :duration (= ?duration {conn.duration})
    :condition (and
        (at start (passenger-at stop-{conn.from_stop}))
        (at start (connection-available {conn_id}))
    )
    :effect (and
        (at start (not (passenger-at stop-{conn.from_stop})))
        (at start (current-trip trip-{trip_clean}))
        (at start (not (connection-available {conn_id})))
        (at end (passenger-at stop-{conn.to_stop}))
    )
)"""
    
    for trans, trans_id in relevant_transfers:
        to_trip_clean = trans.to_trip.replace("-", "_")
        durative_actions += f"""
(:durative-action make-{trans_id}
    :parameters ()
    :duration (= ?duration {trans.transfer_time})
    :condition (and
        (at start (passenger-at stop-{trans.stop_id}))
        (at start (transfer-available {trans_id}))
    )
    :effect (and
        (at start (current-trip trip-{to_trip_clean}))
        (at start (not (transfer-available {trans_id})))
        (at end (passenger-at stop-{trans.stop_id}))
    )
)"""
    
    # Write problem with durative actions
    full_content = problem_content + durative_actions + "\n)"
    
    with open(output_path, 'w') as f:
        f.write(full_content)

def gtfs_to_pddl(
    origin: str,
    destination: str,
    start_time: str = "08:00:00",
    data_dir: Path = Path("public/data"),
    output_dir: Path = Path("pddl_output")
) -> Tuple[Path, Path]:
    """
    Convert GTFS data to PDDL domain and problem files with transfer support.
    """
    output_dir.mkdir(exist_ok=True)
    
    # Load GTFS data
    stops, routes, trips, stop_times_by_trip = load_gtfs_data(data_dir)
    
    # Validate stops
    if origin not in stops:
        raise ValueError(f"Origin stop not found: {origin}")
    if destination not in stops:
        raise ValueError(f"Destination stop not found: {destination}")
    
    # Extract connections and transfers
    connections = extract_trip_connections(stops, routes, trips, stop_times_by_trip)
    transfers = extract_transfers(stops, trips, stop_times_by_trip)
    
    # Generate PDDL files
    domain_file = output_dir / "train-domain.pddl"
    problem_file = output_dir / f"train-problem-{origin}-to-{destination}.pddl"
    
    print("Generating PDDL domain...")
    generate_pddl_domain(domain_file)
    
    print("Generating PDDL problem...")
    generate_pddl_problem(
        connections,
        transfers,
        origin,
        destination,
        start_time,
        stops,
        routes,
        trips,
        problem_file
    )
    
    # Statistics
    start_minutes = parse_time_to_minutes(start_time)
    relevant_connections = sum(1 for conn in connections 
                              if parse_time_to_minutes(conn.departure_time) >= start_minutes)
    relevant_transfers = sum(1 for trans in transfers 
                            if parse_time_to_minutes(trans.departure_time) >= start_minutes)
    
    print(f"\nGenerated PDDL files:")
    print(f"Domain: {domain_file}")
    print(f"Problem: {problem_file}")
    print(f"Origin: {stops[origin]['stop_name']} ({origin})")
    print(f"Destination: {stops[destination]['stop_name']} ({destination})")
    print(f"Total connections: {len(connections)} (relevant: {relevant_connections})")
    print(f"Total transfers: {len(transfers)} (relevant: {relevant_transfers})")
    print(f"\nTo solve with OPTIC:")
    print(f"optic {domain_file} {problem_file}")
    
    return domain_file, problem_file

def generate_simple_pddl_domain(output_path: Path) -> None:
    """Generate a simpler PDDL domain file."""
    
    domain_content = """(define (domain simple-train-journey)
    (:requirements :strips :typing :durative-actions :timed-initial-literals)
    
    (:types
        stop - object
        trip - object
    )
    
    (:predicates
        (at-stop ?stop - stop)
        (on-trip ?trip - trip)
        (trip-connects ?trip - trip ?from ?to - stop)
        (trip-available ?trip - trip ?from - stop)
    )
    
    (:functions
        (travel-time ?trip - trip ?from ?to - stop)
    )
    
    (:durative-action board-and-travel
        :parameters (?trip - trip ?from ?to - stop)
        :duration (= ?duration (travel-time ?trip ?from ?to))
        :condition (and
            (at start (at-stop ?from))
            (at start (trip-connects ?trip ?from ?to))
            (at start (trip-available ?trip ?from))
        )
        :effect (and
            (at start (not (at-stop ?from)))
            (at start (on-trip ?trip))
            (at start (not (trip-available ?trip ?from)))
            (at end (not (on-trip ?trip)))
            (at end (at-stop ?to))
        )
    )
    
    (:durative-action wait
        :parameters (?stop - stop)
        :duration (= ?duration 5)
        :condition (at start (at-stop ?stop))
        :effect (and)
    )
)"""
    
    with open(output_path, 'w') as f:
        f.write(domain_content)

def generate_simple_pddl_problem(
    connections: List[TripConnection],
    origin_stop: str,
    destination_stop: str,
    start_time: str,
    stops: Dict,
    output_path: Path,
    max_connections: int = 50  # Limit for testing
) -> None:
    """Generate a much smaller PDDL problem for testing."""
    
    start_minutes = parse_time_to_minutes(start_time)
    
    # Filter and limit connections for testing
    relevant_connections = []
    for conn in connections:
        dep_minutes = parse_time_to_minutes(conn.departure_time)
        if dep_minutes >= start_minutes and len(relevant_connections) < max_connections:
            # Only include connections involving our origin/destination or nearby stops
            if (conn.from_stop == origin_stop or conn.to_stop == destination_stop or 
                conn.from_stop == destination_stop or conn.to_stop == origin_stop):
                relevant_connections.append(conn)
    
    # If we don't have direct connections, add some more
    if len(relevant_connections) < 10:
        for conn in connections:
            dep_minutes = parse_time_to_minutes(conn.departure_time)
            if dep_minutes >= start_minutes and len(relevant_connections) < max_connections:
                relevant_connections.append(conn)
    
    # Extract unique objects
    all_stops = {origin_stop, destination_stop}
    all_trips = set()
    
    for conn in relevant_connections:
        all_stops.add(conn.from_stop)
        all_stops.add(conn.to_stop)
        all_trips.add(conn.trip_id)
    
    problem_content = f"""(define (problem simple-train-problem)
    (:domain simple-train-journey)
    
    (:objects
        ;; Stops (limited set)
        {' '.join(f'stop_{stop}' for stop in sorted(list(all_stops)[:20]))} - stop
        
        ;; Trips (limited set)
        {' '.join(f'trip_{trip.replace("-", "_")}' for trip in sorted(list(all_trips)[:20]))} - trip
    )
    
    (:init
        ;; Start at origin
        (at-stop stop_{origin_stop})
        
        ;; Trip connections
"""

    # Add connections with travel times
    for conn in relevant_connections:
        trip_clean = conn.trip_id.replace("-", "_")
        if f'trip_{trip_clean}' in problem_content and f'stop_{conn.from_stop}' in problem_content and f'stop_{conn.to_stop}' in problem_content:
            problem_content += f"        (trip-connects trip_{trip_clean} stop_{conn.from_stop} stop_{conn.to_stop})\n"
            problem_content += f"        (= (travel-time trip_{trip_clean} stop_{conn.from_stop} stop_{conn.to_stop}) {conn.duration})\n"
            
            # Make trip available at departure time
            dep_minutes = parse_time_to_minutes(conn.departure_time)
            relative_time = dep_minutes - start_minutes
            if relative_time >= 0:
                problem_content += f"        (at {relative_time} (trip-available trip_{trip_clean} stop_{conn.from_stop}))\n"

    problem_content += f"""
    )
    
    (:goal
        (at-stop stop_{destination_stop})
    )
    
    (:metric minimize (total-time))
)"""

    with open(output_path, 'w') as f:
        f.write(problem_content)

def create_test_pddl(
    origin: str = "830012810",
    destination: str = "830012852", 
    start_time: str = "08:00:00",
    data_dir: Path = Path("public/data"),
    output_dir: Path = Path("pddl_test")
) -> Tuple[Path, Path]:
    """Create a small test PDDL problem."""
    
    output_dir.mkdir(exist_ok=True)
    
    # Load minimal data
    stops, routes, trips, stop_times_by_trip = load_gtfs_data(data_dir)
    
    # Extract only a subset of connections
    connections = extract_trip_connections(stops, routes, trips, stop_times_by_trip)
    
    print(f"Total connections in dataset: {len(connections)}")
    
    # Generate small test files
    domain_file = output_dir / "test-domain.pddl"
    problem_file = output_dir / f"test-problem.pddl"
    
    generate_simple_pddl_domain(domain_file)
    generate_simple_pddl_problem(
        connections,
        origin,
        destination,
        start_time,
        stops,
        problem_file,
        max_connections=20  # Very small for testing
    )
    
    print(f"Generated test files:")
    print(f"Domain: {domain_file}")
    print(f"Problem: {problem_file}")
    
    # Show file sizes
    domain_size = domain_file.stat().st_size
    problem_size = problem_file.stat().st_size
    
    print(f"Domain file size: {domain_size} bytes")
    print(f"Problem file size: {problem_size} bytes")
    print(f"Problem file lines: {len(open(problem_file).readlines())}")
    
    return domain_file, problem_file

# Example usage and testing
if __name__ == "__main__":
    try:
        print("Converting GTFS to PDDL with transfer support...")
        
        domain_file, problem_file = gtfs_to_pddl(
            origin="830012810",      # CAGLIARI S.GILLA from your data
            destination="830012852", # GOLFO ARANCI from your data
            start_time="08:00:00"
        )
        
        print(f"\nSample OPTIC commands:")
        print(f"optic {domain_file} {problem_file}")
        print(f"optic {domain_file} {problem_file} > solution.txt")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Test with very simple case
if __name__ == "__main__":
    try:
        print("Creating small test PDDL files...")
        
        domain_file, problem_file = create_test_pddl()
        
        print(f"\nTo test with OPTIC:")
        print(f"optic {domain_file} {problem_file}")
        
        # Show the actual problem content (first 50 lines)
        print(f"\nFirst 30 lines of problem file:")
        with open(problem_file, 'r') as f:
            for i, line in enumerate(f):
                if i < 30:
                    print(f"{i+1:2d}: {line.rstrip()}")
                else:
                    break
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()