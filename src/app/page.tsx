"use client";

import { JourneyPlanner } from "@/components/journey-planner/JourneyPlanner";
import {
    fetchRouteForStops,
    fetchRoutes,
    fetchStops,
    fetchStopTimes,
    PlanningResult,
    Route,
    RouteStop,
} from "@/components/utility/QueryService";
import { Box, Card, HStack, Spinner, VStack } from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

// Dynamically import MapView with SSR disabled
const MapView = dynamic(() => import("../components/MapView"), { ssr: false });

export type JourneySearch = {
    from: string;
    to: string;
    date: string;
    time: string;
};

export default function Home() {
    // Data fetching

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

    // State
    const [selectedRoute, setSelectedRoute] = useState<Route | null>(null);
    const [selectedStops, setSelectedStops] = useState<string[]>([]);
    const [journeySearch, setJourneySearch] = useState<JourneySearch>({
        from: "",
        to: "",
        date: new Date().toISOString().split("T")[0],
        time: "08:00:00",
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

    const handleJourneyPlan = async () => {
        if (!journeySearch.from || !journeySearch.to) return;

        setIsPlanning(true);
        setPlanningResult(null);

        setTimeout(() => {
            const route = fetchRouteForStops(
                journeySearch.from,
                journeySearch.to,
                journeySearch.time
            );
            route.then((r) => {
                console.log("Fetched route for journey:", r);
                setPlanningResult(r);
                setSelectedStops(
                    r.detailed_route.map((stop: RouteStop) => stop.stop_id)
                );
                setIsPlanning(false);
            });
        }, 1);
    };

    const isLoading = stopsLoading || routesLoading || stopTimesLoading;

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
                            mapCenter={mapCenter}
                            planningResult={planningResult}
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
                {/*  <RouteExplorer
                    routes={routes}
                    selectedStops={selectedStops}
                    setSelectedRoute={setSelectedRoute}
                    selectedRoute={selectedRoute}
                /> */}

                {/* Journey Planner */}
                <JourneyPlanner
                    stops={stops}
                    journeySearch={journeySearch}
                    setJourneySearch={setJourneySearch}
                    handleJourneyPlan={handleJourneyPlan}
                    isPlanning={isPlanning}
                    planningResult={planningResult}
                />
            </VStack>
        </HStack>
    );
}
