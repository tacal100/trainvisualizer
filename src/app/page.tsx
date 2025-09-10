"use client";

import DateTimePicker from "@/components/DateTimePicker";
import ResultsBox from "@/components/ResultsBox";
import RouteExplorer from "@/components/RouteExplorer";
import StopPicker from "@/components/StopPicker";
import {
    Box,
    Button,
    Card,
    HStack,
    Icon,
    Separator,
    Spinner,
    VStack,
} from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import Papa from "papaparse";
import { useEffect, useState } from "react";
import { LuNavigation } from "react-icons/lu";

// Dynamically import MapView with SSR disabled
const MapView = dynamic(() => import("../components/MapView"), { ssr: false });

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

export type JourneySegment = {
    route: string;
    routeColor: string;
    from: string;
    to: string;
    departure: string;
    arrival: string;
    stops: string[];
};

export type JourneySearch = {
    from: string;
    to: string;
    date: string;
    time: string;
};

export type PlanningResult = {
    journeys: Array<{
        duration: number;
        segments: JourneySegment[];
        transfers: number;
    }>;
    success?: boolean;
};

const parseCSV = (csvText: string) => {
    const result = Papa.parse(csvText, {
        header: true,
        skipEmptyLines: true,
        dynamicTyping: false,
    });
    return result.data;
};

export default function Home() {
    // Data fetching
    const fetchStops = async (): Promise<Stop[]> => {
        const res = await fetch("/data/stops.csv");
        const csvText = await res.text();
        const parsed = parseCSV(csvText);
        return parsed.filter(
            (stop: any) => stop.stop_lat && stop.stop_lon
        ) as Stop[];
    };

    const fetchRoutes = async (): Promise<Route[]> => {
        const res = await fetch("/data/routes.csv");
        const csvText = await res.text();
        const parsed = parseCSV(csvText);
        return parsed as Route[];
    };

    const fetchStopTimes = async (): Promise<StopTime[]> => {
        const res = await fetch("/data/stop_times.csv");
        const csvText = await res.text();
        const parsed = parseCSV(csvText);
        return parsed as StopTime[];
    };

    const fetchTrips = async (): Promise<Trip[]> => {
        const res = await fetch("/data/trips.csv");
        const csvText = await res.text();
        const parsed = parseCSV(csvText);
        return parsed as Trip[];
    };

    const fetchStopsJson = async (): Promise<string[]> => {
        const res = await fetch("/data/suggested_route.json");
        const json = await res.json();
        console.log("Fetched suggested stops:", json);
        return json.stops();
    };

    // Queries
    const { data: stops = [], isLoading: stopsLoading } = useQuery({
        queryKey: ["stops"],
        queryFn: fetchStops,
        staleTime: Infinity,
    });

    const { data: routes = [], isLoading: routesLoading } = useQuery({
        queryKey: ["routes"],
        queryFn: fetchRoutes,
        staleTime: Infinity,
    });

    const { data: stopTimes = [], isLoading: stopTimesLoading } = useQuery({
        queryKey: ["stopTimes"],
        queryFn: fetchStopTimes,
        staleTime: Infinity,
    });

    const { data: trips = [], isLoading: tripsLoading } = useQuery({
        queryKey: ["trips"],
        queryFn: fetchTrips,
        staleTime: Infinity,
    });

    // State
    const [selectedRoute, setSelectedRoute] = useState<Route | null>(null);
    const [selectedStops, setSelectedStops] = useState<string[]>([]);
    const [journeySearch, setJourneySearch] = useState<JourneySearch>({
        from: "",
        to: "",
        date: "",
        time: "",
    });
    const [planningResult, setPlanningResult] = useState<PlanningResult | null>(
        null
    );
    const [isPlanning, setIsPlanning] = useState(false);
    const [mounted, setMounted] = useState(false);

    // Map center
    const mapCenter: [number, number] = [
        stops[0] ? parseFloat(stops[0].stop_lat) : 45.4642,
        stops[0] ? parseFloat(stops[0].stop_lon) : 9.19,
    ];
    useEffect(() => {
        setMounted(true);
    }, []);

    // Get stops for selected route
    useEffect(() => {
        if (selectedRoute && trips.length > 0 && stopTimes.length > 0) {
            const routeTrips = trips.filter(
                (t) => t.route_id === selectedRoute.route_id
            );
            console.log("Route trips:", routeTrips);
            if (routeTrips.length > 0) {
                // Collect all stop_ids from all trips for this route
                const allStopIds = new Set<string>();
                routeTrips.forEach((trip) => {
                    stopTimes
                        .filter((st) => st.trip_id === trip.trip_id)
                        .forEach((st) => {
                            allStopIds.add(st.stop_id);
                        });
                });
                setSelectedStops(Array.from(allStopIds));
            }
        } else {
            setSelectedStops([]);
        }
    }, [selectedRoute, trips, stopTimes]);

    const handleJourneyPlan = async () => {
        if (!journeySearch.from || !journeySearch.to) return;

        setIsPlanning(true);
        setPlanningResult(null);

        setTimeout(() => {
            const fromStop = stops.find(
                (s) => s.stop_id === journeySearch.from
            );
            const toStop = stops.find((s) => s.stop_id === journeySearch.to);

            // replace with pddl planner logic
            setPlanningResult({
                success: true,
                journeys: [
                    {
                        duration: 45,
                        transfers: 0,
                        segments: [
                            {
                                route: "REG",
                                routeColor: "#FF0000",
                                from: fromStop?.stop_name || "Unknown",
                                to: toStop?.stop_name || "Unknown",
                                departure: "10:15",
                                arrival: "11:00",
                                stops: [journeySearch.from, journeySearch.to],
                            },
                        ],
                    },
                    {
                        duration: 65,
                        transfers: 1,
                        segments: [
                            {
                                route: "BUS",
                                routeColor: "#00AA00",
                                from: fromStop?.stop_name || "Unknown",
                                to: "Milano Centrale",
                                departure: "10:00",
                                arrival: "10:30",
                                stops: [journeySearch.from, "central_station"],
                            },
                            {
                                route: "REG",
                                routeColor: "#FF0000",
                                from: "Milano Centrale",
                                to: toStop?.stop_name || "Unknown",
                                departure: "10:45",
                                arrival: "11:05",
                                stops: ["central_station", journeySearch.to],
                            },
                        ],
                    },
                ],
            });
            setIsPlanning(false);
        }, 1);
    };

    const isLoading =
        stopsLoading || routesLoading || stopTimesLoading || tripsLoading;

    console.log(routes);

    return (
        <HStack
            h={"100vh"}
            w={"100vw"}
            gap={4}
            alignItems="stretch"
            padding={4}
        >
            <Card.Root w={"65%"}>
                <Card.Header>
                    <Card.Title>Train Journey Planner</Card.Title>
                    <Card.Description>
                        Plan your train journeys in Sardinia
                    </Card.Description>
                </Card.Header>
                <Card.Body h={"100%"}>
                    {mounted && !isLoading ? (
                        <MapView
                            stops={stops}
                            selectedRoute={selectedRoute}
                            selectedStops={selectedStops}
                            mapCenter={mapCenter}
                            journeySegments={
                                planningResult?.journeys[0]?.segments
                            }
                        />
                    ) : (
                        <Box
                            display="flex"
                            alignItems="center"
                            justifyContent="center"
                            h="100%"
                        >
                            <Spinner size="xl" />
                        </Box>
                    )}
                </Card.Body>
            </Card.Root>

            <VStack w={"35%"} gap={4} alignItems="stretch" className="flex">
                {/* Route Explorer */}
                <RouteExplorer
                    routes={routes}
                    selectedStops={selectedStops}
                    setSelectedRoute={setSelectedRoute}
                    selectedRoute={selectedRoute}
                />

                {/* Journey Planner */}
                <Card.Root flex={1} display="flex" flexDir="column" minH={0}>
                    <Card.Header>
                        <Card.Title className="flex items-center gap-2">
                            <Icon>
                                <LuNavigation />
                            </Icon>
                            Journey Planner
                        </Card.Title>
                    </Card.Header>
                    <Card.Body
                        flex={1}
                        display="flex"
                        flexDir="column"
                        minH={0}
                    >
                        <VStack gap={3}>
                            <StopPicker
                                stops={stops}
                                journeySearch={journeySearch}
                                setJourneySearch={setJourneySearch}
                                from={true}
                            />
                            <StopPicker
                                stops={stops}
                                journeySearch={journeySearch}
                                setJourneySearch={setJourneySearch}
                                from={false}
                            />

                            <DateTimePicker
                                journeySearch={journeySearch}
                                setJourneySearch={setJourneySearch}
                            />

                            <Button
                                w="full"
                                onClick={handleJourneyPlan}
                                disabled={
                                    !journeySearch.from ||
                                    !journeySearch.to ||
                                    isPlanning
                                }
                                loading={isPlanning}
                            >
                                Find Journey
                            </Button>
                        </VStack>
                        <Separator marginBlock={4} />
                        {/* Results */}
                        {planningResult && (
                            <ResultsBox planningResult={planningResult} />
                        )}
                    </Card.Body>
                </Card.Root>
            </VStack>
        </HStack>
    );
}
