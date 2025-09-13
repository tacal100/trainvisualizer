import { useEffect, useRef } from "react";
import { CircleMarker, Popup } from "react-leaflet";
import { RouteStop, Stop } from "../utility/QueryService";

/** Component to manage popup state for selected stops */
export function StopMarker({
    stop,
    isHighlighted,
    selectedStop,
    isInJourney,
    routeStop,
    setSelectedStop,
}: {
    stop: Stop;
    isHighlighted: boolean;
    selectedStop?: RouteStop;
    isInJourney: boolean;
    routeStop?: RouteStop;
    setSelectedStop: React.Dispatch<
        React.SetStateAction<RouteStop | undefined>
    >;
}) {
    const markerRef = useRef<L.CircleMarker>(null);

    useEffect(() => {
        if (isHighlighted && markerRef.current) {
            markerRef.current.openPopup();
        }
    }, [isHighlighted]);

    return (
        <CircleMarker
            ref={markerRef}
            center={[parseFloat(stop.stop_lat), parseFloat(stop.stop_lon)]}
            radius={isHighlighted ? 10 : isInJourney ? 7 : 6}
            pathOptions={{
                fillColor: isHighlighted
                    ? "#2D3748"
                    : isInJourney
                    ? "#666"
                    : "#0066CC",
                fillOpacity: 0.8,
                color: isHighlighted ? "#2D3748" : "white",
                weight: isHighlighted ? 3 : 2,
            }}
            eventHandlers={{
                click: () => {
                    if (routeStop) {
                        setSelectedStop(routeStop);
                    }
                },
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
                    {isHighlighted && (
                        <>
                            <br />
                            <span
                                style={{
                                    fontSize: "12px",
                                    color: "#0066CC",
                                    fontWeight: "bold",
                                }}
                            >
                                {selectedStop?.arrival_time +
                                    " - " +
                                    selectedStop?.departure_time}
                            </span>
                        </>
                    )}
                </div>
            </Popup>
        </CircleMarker>
    );
}
