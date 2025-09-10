export type routeStop = {
    arrival_time: string;
    departure_time: string;
    is_transfer: boolean;
    route_description: string;
    route_id: string;
    route_name: string;
    stop_id: string;
    stop_name: string;
};

export type PlanningResult = {
    arrival_time: string;
    destination_id: string;
    destination_name: string;
    detailed_route: routeStop[];
    origin_id: string;
    origin_name: string;
    start_time: string;
    stops_count: number;
    transfers: string[];
};

export function fetchRouteForStops(from: string, to: string) {
    const url = `http://localhost:8080/api/route?from=${encodeURIComponent(
        from
    )}&to=${encodeURIComponent(to)}`;
    return fetch(url).then((res) => {
        if (!res.ok) {
            throw new Error("Network response was not ok");
        }
        return res.json();
    });
}
