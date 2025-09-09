import L from "leaflet";
import { useEffect } from "react";
import {
    CircleMarker,
    MapContainer,
    Polyline,
    Popup,
    TileLayer,
    useMap,
} from "react-leaflet";
// @ts-ignore
import iconUrl from "leaflet/dist/images/marker-icon.png";
// @ts-ignore
import iconShadowUrl from "leaflet/dist/images/marker-shadow.png";

type Stop = {
    stop_id: string;
    stop_name: string;
    stop_lat: string;
    stop_lon: string;
};

type Route = {
    route_id: string;
    route_short_name: string;
    route_long_name: string;
    route_color: string;
};

type JourneySegment = {
    route: string;
    routeColor: string;
    from: string;
    to: string;
    departure: string;
    arrival: string;
    stops: string[];
};

interface MapViewProps {
    stops: Stop[];
    selectedRoute: Route | null;
    selectedStops: string[];
    mapCenter: [number, number];
    journeySegments?: JourneySegment[];
}

// Fix Leaflet default icon
let DefaultIcon = L.icon({
    iconUrl: iconUrl.src,
    shadowUrl: iconShadowUrl.src,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

function MapBounds({
    stops,
    selectedStops,
}: {
    stops: Stop[];
    selectedStops: string[];
}) {
    const map = useMap();

    useEffect(() => {
        if (selectedStops.length > 0) {
            const selectedStopObjects = stops.filter((s) =>
                selectedStops.includes(s.stop_id)
            );
            if (selectedStopObjects.length > 0) {
                const bounds = L.latLngBounds(
                    selectedStopObjects.map((s) => [
                        parseFloat(s.stop_lat),
                        parseFloat(s.stop_lon),
                    ])
                );
                map.fitBounds(bounds, { padding: [50, 50] });
            }
        }
    }, [selectedStops, stops, map]);

    return null;
}

/**
 * Map view component to visualize stops, routes, and journeys.
 */
export default function MapView({
    stops,
    selectedRoute,
    selectedStops,
    mapCenter,
    journeySegments,
}: MapViewProps) {
    // Get route polyline positions
    const getRoutePositions = (): [number, number][] => {
        if (!selectedStops || selectedStops.length < 2) return [];

        return selectedStops
            .map((stopId) => {
                const stop = stops.find((s) => s.stop_id === stopId);
                if (!stop) return null;
                return [
                    parseFloat(stop.stop_lat),
                    parseFloat(stop.stop_lon),
                ] as [number, number];
            })
            .filter((pos): pos is [number, number] => pos !== null);
    };

    // Get journey polyline for planned routes
    const getJourneyPolylines = () => {
        if (!journeySegments) return [];

        return journeySegments.map((segment, idx) => {
            const positions = segment.stops
                .map((stopId) => {
                    const stop = stops.find(
                        (s) => s.stop_id === stopId || s.stop_name === stopId
                    );
                    if (!stop) return null;
                    return [
                        parseFloat(stop.stop_lat),
                        parseFloat(stop.stop_lon),
                    ] as [number, number];
                })
                .filter((pos): pos is [number, number] => pos !== null);

            return {
                positions,
                color: segment.routeColor,
                key: `journey-${idx}`,
            };
        });
    };

    const routePositions = getRoutePositions();
    const journeyPolylines = getJourneyPolylines();

    return (
        <MapContainer
            center={mapCenter}
            zoom={10}
            style={{ height: "inherit", width: "inherit", minHeight: 500 }}
        >
            <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution="&copy; OpenStreetMap contributors"
            />

            <MapBounds stops={stops} selectedStops={selectedStops} />

            {/* Route visualization */}
            {selectedRoute && routePositions.length > 1 && (
                <Polyline
                    positions={routePositions}
                    pathOptions={{
                        color: selectedRoute.route_color || "#0066CC",
                        weight: 5,
                        opacity: 0.7,
                    }}
                />
            )}

            {journeyPolylines.map((polyline) => (
                <Polyline
                    key={polyline.key}
                    positions={polyline.positions}
                    pathOptions={{
                        color: polyline.color,
                        weight: 6,
                        opacity: 0.8,
                        dashArray: "10, 10",
                    }}
                />
            ))}

            {/* All stops */}
            {stops.map((stop) => {
                const isSelected = selectedStops.includes(stop.stop_id);
                const isInJourney = journeySegments?.some(
                    (seg) =>
                        seg.stops.includes(stop.stop_id) ||
                        seg.stops.includes(stop.stop_name)
                );

                if (isSelected || isInJourney) {
                    return (
                        <CircleMarker
                            key={stop.stop_id}
                            center={[
                                parseFloat(stop.stop_lat),
                                parseFloat(stop.stop_lon),
                            ]}
                            radius={isInJourney ? 10 : 8}
                            pathOptions={{
                                fillColor: isInJourney
                                    ? "#FF6B6B"
                                    : selectedRoute?.route_color || "#0066CC",
                                fillOpacity: 0.8,
                                color: "white",
                                weight: 3,
                            }}
                        >
                            <Popup>
                                <div>
                                    <strong>{stop.stop_name}</strong>
                                    <br />
                                    <span
                                        style={{
                                            fontSize: "12px",
                                            color: "#666",
                                        }}
                                    >
                                        ID: {stop.stop_id}
                                    </span>
                                    {isSelected && selectedRoute && (
                                        <>
                                            <br />
                                            <span
                                                style={{
                                                    fontSize: "12px",
                                                    color: selectedRoute.route_color,
                                                    fontWeight: "bold",
                                                }}
                                            >
                                                {selectedRoute.route_short_name}
                                            </span>
                                        </>
                                    )}
                                </div>
                            </Popup>
                        </CircleMarker>
                    );
                } else {
                    return (
                        <CircleMarker
                            key={stop.stop_id}
                            center={[
                                parseFloat(stop.stop_lat),
                                parseFloat(stop.stop_lon),
                            ]}
                            radius={5}
                            pathOptions={{
                                fillColor: "#666",
                                fillOpacity: 0.5,
                                color: "white",
                                weight: 2,
                            }}
                        >
                            <Popup>
                                <div>
                                    <strong>{stop.stop_name}</strong>
                                    <br />
                                    <span
                                        style={{
                                            fontSize: "12px",
                                            color: "#666",
                                        }}
                                    >
                                        ID: {stop.stop_id}
                                    </span>
                                </div>
                            </Popup>
                        </CircleMarker>
                    );
                }
            })}
        </MapContainer>
    );
}
