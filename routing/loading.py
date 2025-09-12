"""
Data loading utilities for GTFS files.

This module contains all functions for loading and parsing GTFS CSV files
including stops, stop_times, routes, and trips data.
"""

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class Stop:
    stop_id: str
    name: str
    lat: float
    lon: float


def load_stops(stops_path: Path) -> Dict[str, Stop]:
    """Load stops from GTFS stops.csv file.
    
    Args:
        stops_path: Path to stops.csv file
        
    Returns:
        Dictionary mapping stop_id to Stop objects
    """
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
    """Load stop times organized by trip from GTFS stop_times.csv file.
    
    Args:
        stop_times_path: Path to stop_times.csv file
        
    Returns:
        Dictionary mapping trip_id to ordered list of stop_times rows
    """
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
    """Load route information from GTFS routes.csv file.
    
    Args:
        routes_path: Path to routes.csv file
        
    Returns:
        Dictionary mapping route_id to route information
    """
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
    """Load trip to route mapping from GTFS trips.csv file.
    
    Args:
        trips_path: Path to trips.csv file
        
    Returns:
        Dictionary mapping trip_id to trip information including route_id
    """
    trip_routes = {}
    try:
        with trips_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                trip_routes[row.get("trip_id", "")] = {
                    "route_id": row.get("route_id", ""),
                    "service_id": row.get("service_id", ""),
                    "trip_headsign": row.get("trip_headsign", ""),
                    "trip_short_name": row.get("trip_short_name", "")
                }
    except FileNotFoundError:
        pass
    return trip_routes


def load_calendar_dates(calendar_dates_path: Path) -> Dict[str, List[str]]:
    """Load service dates from GTFS calendar_dates.csv file.
    
    Args:
        calendar_dates_path: Path to calendar_dates.csv file
        
    Returns:
        Dictionary mapping service_id to list of dates (YYYYMMDD)
    """
    service_dates = defaultdict(list)
    try:
        with calendar_dates_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # exception_type 1 means service is added for this date
                if row.get("exception_type") == "1":
                    service_dates[row["service_id"]].append(row["date"])
    except FileNotFoundError:
        pass
    return service_dates
