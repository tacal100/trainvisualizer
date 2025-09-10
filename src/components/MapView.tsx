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
import { PlanningResult, Route, Stop } from "./utility/QueryService";

interface MapViewProps {
    stops: Stop[];
    selectedRoute: Route | null;
    mapCenter: [number, number];
    planningResult: PlanningResult | null;
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

function MapBounds({ selectedStops }: { selectedStops: Stop[] | undefined }) {
    const map = useMap();

    useEffect(() => {
        if (selectedStops && selectedStops.length > 0) {
            const bounds = L.latLngBounds(
                selectedStops.map((s) => [
                    parseFloat(s.stop_lat),
                    parseFloat(s.stop_lon),
                ])
            );
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [selectedStops, map]);

    return null;
}

/**
 * Map view component to visualize stops, routes, and journeys.
 */
export default function MapView({
    stops,
    selectedRoute,
    mapCenter,
    planningResult,
}: MapViewProps) {
    // Get route polyline positions
    /*   const getRoutePositions = (): [number, number][] => {
        //TODO: we need a backend function that returns all stops in a route
     }; */

    const getJourneyPolylinesWithRouteColors = () => {
        if (!planningResult || planningResult.detailed_route.length < 2)
            return [];

        const polylines = [];
        let currentSegment = [planningResult.detailed_route[0]];

        planningResult.detailed_route.map((stop, i) => {
            // collect stops until a transfer is found
            if (!stop.is_transfer) {
                currentSegment.push(stop);
            } else {
                if (currentSegment.length >= 2) {
                    const positions = currentSegment.map(
                        (s) =>
                            [
                                parseFloat(s.stop_lat),
                                parseFloat(s.stop_lon),
                            ] as [number, number]
                    );
                    // push all collected stops until transfer as a polyline
                    polylines.push({
                        positions,
                        color: `hsl(${(i * 60) % 360}, 70%, 50%)`,
                        key: `journey-segment-${i}`,
                    });
                }

                // start new segment
                currentSegment = [
                    currentSegment[currentSegment.length - 1],
                    stop,
                ];
            }
        });

        // add final segment
        if (currentSegment.length >= 2) {
            const positions = currentSegment.map(
                (s) =>
                    [parseFloat(s.stop_lat), parseFloat(s.stop_lon)] as [
                        number,
                        number
                    ]
            );

            polylines.push({
                positions,
                color: "#FF6B6B",
                key: `journey-segment-final`,
            });
        }

        return polylines;
    };

    // const routePositions = getRoutePositions();
    const journeyPolylines = getJourneyPolylinesWithRouteColors();

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

            <MapBounds selectedStops={planningResult?.detailed_route} />

            {/* Route visualization */}
            {/*  {selectedRoute && routePositions.length > 1 && (
                <Polyline
                    positions={routePositions}
                    pathOptions={{
                        color: "#0066CC",
                        weight: 5,
                        opacity: 0.7,
                    }}
                />
            )} */}

            {/* Journey visualization */}
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
                const isSelected = planningResult?.detailed_route.some(
                    (s) => s.stop_id === stop.stop_id
                );
                const isInJourney = planningResult?.detailed_route.some(
                    (stopInJourney) =>
                        stop.stop_id === stopInJourney.stop_id ||
                        stop.stop_name === stopInJourney.stop_name
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
                                fillColor: isInJourney ? "#FF6B6B" : "#0066CC",
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
                                                    color: "#0066CC",
                                                    fontWeight: "bold",
                                                }}
                                            >
                                                {selectedRoute.route_long_name}
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
