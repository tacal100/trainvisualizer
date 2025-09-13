"use client";
import { Badge, Box, Card, Text, VStack } from "@chakra-ui/react";
import { BsArrowLeftRight } from "react-icons/bs";
import { PlanningResult, RouteStop } from "../utility/QueryService";

type JourneyResultsProps = {
    selectedStop?: RouteStop;
    setSelectedStop: React.Dispatch<
        React.SetStateAction<RouteStop | undefined>
    >;
    planningResult: PlanningResult;
};

export default function JourneyResults({
    selectedStop,
    setSelectedStop,
    planningResult,
}: JourneyResultsProps) {
    // Map each stop to its segment index
    const segmentIndices = planningResult.detailed_route.map((_, idx) => {
        let segmentIndex = 0;
        for (let i = 0; i < idx; i++) {
            if (planningResult.detailed_route![i].is_transfer) {
                segmentIndex++;
            }
        }
        return segmentIndex;
    });
    const travelMins = planningResult.total_travel_minutes;
    console.log(travelMins);
    return (
        <Box className="flex flex-col" minH={0} gap={4}>
            <div className="flex flex-row w-full justify-between items-center !border-b !pb-4">
                <div className="flex flex-col gap-2">
                    <Text fontWeight="semibold">Recommended Journey:</Text>
                    <Text color={"gray.400"}>
                        Travel Time: {toHoursAndMinutes(travelMins)}
                    </Text>
                </div>
                <div className="flex flex-col gap-2">
                    <>
                        <Badge background="green.500" size="md">
                            <Text fontWeight="semibold">
                                {planningResult.stop_count} Stop
                                {planningResult.stop_count !== 1 ? "s" : ""}
                            </Text>
                        </Badge>
                        <Badge background="red.500" size="md">
                            <Text fontWeight="semibold">
                                {planningResult.transfers.length} Transfer
                                {planningResult.transfers.length !== 1
                                    ? "s"
                                    : ""}
                            </Text>
                        </Badge>
                    </>
                </div>
            </div>
            <VStack
                gap={4}
                overflow={"hidden"}
                overflowY={"auto"}
                p={4}
                bg={"gray.900"}
                borderRadius={"md"}
            >
                {planningResult.detailed_route.map((stop, idx) => (
                    <StopCard
                        selectedStop={selectedStop}
                        setSelectedStop={setSelectedStop}
                        stop={stop}
                        idx={idx}
                        segmentIndex={segmentIndices[idx]}
                        key={idx}
                    />
                ))}
            </VStack>
        </Box>
    );
}

type StopCardProps = {
    stop: RouteStop;
    idx: number;
    segmentIndex: number;
    setSelectedStop: React.Dispatch<
        React.SetStateAction<RouteStop | undefined>
    >;
    selectedStop?: RouteStop;
};

function StopCard({
    stop,
    segmentIndex,
    setSelectedStop,
    selectedStop,
}: StopCardProps) {
    return (
        <Box className="flex flex-col items-center w-full gap-3">
            {stop.is_transfer ? <BsArrowLeftRight /> : null}
            <Card.Root
                className="transition-transform duration-150 hover:scale-[1.01] transform-gpu will-change-transform"
                style={{
                    borderColor: `hsl(${
                        (stop.is_transfer
                            ? 100 + (segmentIndex + 1) * 50
                            : 100 + segmentIndex * 50) % 360
                    }, 50%, 50%)`,
                    backgroundColor: isSameStop(selectedStop, stop)
                        ? "#2D3748"
                        : "#1A202C",
                    borderWidth: isSameStop(selectedStop, stop) ? 3 : 2,
                    cursor: "pointer",
                    transformOrigin: "center",
                }}
                onClick={() => setSelectedStop(stop)}
                w="full"
                p={0}
            >
                <Card.Header>
                    <div className="flex flex-row justify-between w-full items-center">
                        <Text fontWeight="bold">{stop.stop_name}</Text>
                        <Text fontSize="sm" color="gray.400">
                            Trip: {stop.trip_headsign}
                        </Text>
                    </div>
                </Card.Header>
                <Card.Body pt={0}>
                    <Text fontSize="sm" color="gray.600">
                        <Text as="p" fontWeight="bold">
                            {stop.trip_short_name
                                ? stop.route_name + "-" + stop.trip_short_name
                                : "N/A"}
                        </Text>
                        {stop.is_transfer ? "Transfer" : "Direct"} - Date:{" "}
                        {parseDate(stop.date)}
                    </Text>
                    <Text fontSize="sm" color="white.800">
                        Arrival: {stop.arrival_time} | Departure:{" "}
                        {stop.departure_time}
                    </Text>
                </Card.Body>
            </Card.Root>
        </Box>
    );
}

function toHoursAndMinutes(totalMinutes: number) {
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    return `${padToTwoDigits(hours)}:${padToTwoDigits(minutes)}`;
}

function padToTwoDigits(num: number) {
    return num.toString().padStart(2, "0");
}

function parseDate(date: string) {
    return date.replace(/(\d{4})(\d{2})(\d{2})/, "$2/$3/$1");
}

function isSameStop(stopA: RouteStop | undefined, stopB: RouteStop) {
    return stopA?.stop_id === stopB.stop_id && stopA?.trip_id === stopB.trip_id;
}
