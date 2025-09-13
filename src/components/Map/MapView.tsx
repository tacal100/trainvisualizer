import L from "leaflet";
import { useEffect, useState } from "react";
import {
    CircleMarker,
    MapContainer,
    Polyline,
    Popup,
    TileLayer,
    useMap,
} from "react-leaflet";
import { PlanningResult, RouteStop, Stop } from "../utility/QueryService";
import { StopMarker } from "./StopMarker";
// Import your train icon properly

interface MapViewProps {
    stops: Stop[];
    mapCenter: [number, number];
    planningResult: PlanningResult | null;
    selectedStop?: RouteStop;
    setSelectedStop: React.Dispatch<
        React.SetStateAction<RouteStop | undefined>
    >;
}

// Fix Leaflet default icon - remove shadow and use your train icon
let DefaultIcon = L.icon({
    iconUrl: "/BSicon_TRAIN2.png", // Handle both Next.js import formats
    iconSize: [25, 25], // Make it square for the train
    iconAnchor: [12, 12], // Center the anchor
    popupAnchor: [0, -12], // Popup appears above the icon
    // Remove shadowUrl and shadowSize completely
});

L.Marker.prototype.options.icon = DefaultIcon;

// Animated marker for journey polylines
function JourneyAnimatedMarker({
    selectedStops,
    polylines,
}: {
    selectedStops: Stop[] | undefined;
    polylines: any[];
}) {
    const map = useMap();
    const [motionLoaded, setMotionLoaded] = useState(false);

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

        if ((L as any).motion) {
            setMotionLoaded(true);
            return;
        }

        // Load the leaflet.motion library

        const script = document.createElement("script");
        script.src =
            "https://cdn.jsdelivr.net/npm/leaflet.motion@0.3.2/dist/leaflet.motion.min.js";
        script.onload = () => setTimeout(() => setMotionLoaded(true), 100);
        document.head.appendChild(script);
    }, []);

    useEffect(() => {
        if (!map || !motionLoaded || polylines.length === 0) return;

        // Create animated sequence using L.motion.seq for different durations per segment
        const motionLayers: any[] = [];

        polylines.forEach((polyline, index) => {
            const segmentDuration = (polyline.duration / 60) * 1000; // Duration in milliseconds because otherwise it takes too long

            const motionLine = (L as any).motion.polyline(
                polyline.positions,
                { color: "transparent" },
                {
                    auto: false,
                    duration: segmentDuration,
                    easing: (L as any).Motion.Ease.linear,
                },
                {
                    showMarker: true,
                    icon: L.divIcon({
                        html: `<div style="background-color: ${polyline.color}; width: 24px; height: 24px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center;">
                                 <img src="/BSicon_TRAIN2.png" style="width: 16px; height: 16px; filter: brightness(0) invert(1);" />
                               </div>`,
                        iconSize: [24, 24],
                        iconAnchor: [12, 12],
                        className: "train-marker",
                    }),
                }
            );

            motionLayers.push(motionLine);
        });

        // Create sequence group to animate segments one after another
        const seqGroup = (L as any).motion.seq(motionLayers, {
            auto: false,
        });

        seqGroup.addTo(map);
        setTimeout(() => seqGroup.motionStart(), 1000);

        return () => {
            seqGroup.motionStop();
            map.removeLayer(seqGroup);
        };
    }, [map, motionLoaded, polylines]);

    return null;
}

/**
 * Map view component to visualize stops, routes, and journeys.
 */
export default function MapView({
    stops,
    mapCenter,
    planningResult,
    selectedStop,
    setSelectedStop,
}: MapViewProps) {
    const selectedStops = planningResult?.detailed_route;

    const getJourneyPolylinesWithRouteColors = () => {
        if (!planningResult || planningResult.detailed_route.length < 2)
            return [];

        const polylines = [];
        let currentSegment = [planningResult.detailed_route[0]];

        // Helper function to convert time string to seconds

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

                    const firstStop = currentSegment[1];
                    const lastStop = currentSegment[currentSegment.length - 1];
                    const startTime = timeToSeconds(firstStop.departure_time);
                    const endTime = timeToSeconds(lastStop.arrival_time);
                    const durationInSeconds = endTime - startTime;

                    // push all collected stops until transfer as a polyline
                    polylines.push({
                        positions,
                        color: `hsl(${
                            100 + ((polylines.length * 50) % 360)
                        }, 70%, 50%)`,
                        key: `journey-segment-${polylines.length}`,
                        duration: durationInSeconds,
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

            // Calculate duration for final segment
            const firstStop = currentSegment[1];
            const lastStop = currentSegment[currentSegment.length - 1];
            const startTime = timeToSeconds(firstStop.departure_time);
            const endTime = timeToSeconds(lastStop.arrival_time);
            const durationInSeconds = endTime - startTime; // Already in seconds

            polylines.push({
                positions,
                color: `hsl(${
                    100 + ((polylines.length * 50) % 360)
                }, 70%, 50%)`,
                key: `journey-segment-${polylines.length}`,
                duration: durationInSeconds,
            });
        }

        return polylines;
    };

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

            {/* Journey visualization */}
            {journeyPolylines.map((polyline) => (
                <Polyline
                    key={polyline.key}
                    positions={polyline.positions}
                    pathOptions={{
                        color: polyline.color,
                        weight: 6,
                        opacity: 0.8,
                    }}
                />
            ))}

            {/* Animated marker along journey */}
            {journeyPolylines.length > 0 && (
                <JourneyAnimatedMarker
                    selectedStops={selectedStops}
                    polylines={journeyPolylines}
                />
            )}

            {/* All stops */}
            {stops.map((stop) => {
                const isInJourney = planningResult?.detailed_route.some(
                    (stopInJourney) =>
                        stop.stop_id === stopInJourney.stop_id ||
                        stop.stop_name === stopInJourney.stop_name
                );
                const isHighlighted = selectedStop?.stop_id === stop.stop_id;
                const routeStop = planningResult?.detailed_route.find(
                    (rs) => rs.stop_id === stop.stop_id
                );

                if (isInJourney) {
                    return (
                        <StopMarker
                            key={stop.stop_id}
                            stop={stop}
                            selectedStop={selectedStop}
                            isHighlighted={isHighlighted}
                            isInJourney={isInJourney}
                            routeStop={routeStop}
                            setSelectedStop={setSelectedStop}
                        />
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
                            pane="markerPane"
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

function timeToSeconds(timeStr: string): number {
    const [hours, minutes, seconds] = timeStr.split(":").map(Number);
    return hours * 3600 + minutes * 60 + seconds;
}
