import Papa from "papaparse";
export type Stop = {
    stop_id: string;
    stop_name: string;
    stop_lat: string;
    stop_lon: string;
};

export type Route = {
    route_id: string;
    route_short_name: string;
    route_long_name: string;
    route_color: string;
    route_text_color?: string;
    route_type?: string;
};

export type StopTime = {
    trip_id: string;
    arrival_time: string;
    departure_time: string;
    stop_id: string;
    stop_sequence: string;
};

export type Trip = {
    trip_id: string;
    route_id: string;
    service_id: string;
    trip_short_name?: string;
};

export type RouteStop = {
    arrival_time: string;
    departure_time: string;
    is_transfer: boolean;
    route_description: string;
    route_id: string;
    route_name: string;
    stop_id: string;
    stop_name: string;
    stop_lat: string;
    stop_lon: string;
    trip_id: string;
};

export type PlanningResult = {
    arrival_time: string;
    destination_id: string;
    destination_name: string;
    detailed_route: RouteStop[];
    origin_id: string;
    origin_name: string;
    start_time: string;
    stop_count: number;
    transfers: string[];
    total_travel_minutes: number;
};

/**
 * Fetches the route between two stops.
 * @param from The starting stop ID.
 * @param to The destination stop ID.
 * @returns A promise that resolves to the route information.
 */
export function fetchRouteForStops(
    from: string,
    to: string,
    time: string
): Promise<PlanningResult> {
    const url = `http://localhost:8080/api/route?from=${encodeURIComponent(
        from
    )}&to=${encodeURIComponent(to)}&time=${encodeURIComponent(time)}`;
    return fetch(url).then((res) => {
        if (!res.ok) {
            throw new Error("Network response was not ok");
        }
        return res.json();
    });
}

function parseCSV(csvText: string) {
    const result = Papa.parse(csvText, {
        header: true,
        skipEmptyLines: true,
        dynamicTyping: false,
    });
    return result.data;
}

export function fetchStops(): Promise<Stop[]> {
    const url = "/data/stops.csv";
    return fetch(url)
        .then((res) => res.text())
        .then((csvText) => {
            const parsed = parseCSV(csvText);
            return parsed as Stop[];
        });
}

export function fetchRoutes(): Promise<Route[]> {
    return fetch("/data/routes.csv")
        .then((res) => res.text())
        .then((csvText) => {
            const parsed = parseCSV(csvText);
            return parsed as Route[];
        });
}

export function fetchStopTimes(): Promise<StopTime[]> {
    return fetch("/data/stop_times.csv")
        .then((res) => res.text())
        .then((csvText) => {
            const parsed = parseCSV(csvText);
            return parsed as StopTime[];
        });
}

export function fetchTrips(): Promise<Trip[]> {
    return fetch("/data/trips.csv")
        .then((res) => res.text())
        .then((csvText) => {
            const parsed = parseCSV(csvText);
            return parsed as Trip[];
        });
}
