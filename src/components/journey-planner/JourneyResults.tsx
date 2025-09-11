"use client";
import { Badge, Box, Card, Text, VStack } from "@chakra-ui/react";
import { BsArrowLeftRight } from "react-icons/bs";
import { PlanningResult, RouteStop } from "../utility/QueryService";

export default function JourneyResults({
    planningResult,
}: {
    planningResult: PlanningResult;
}) {
    // Map each stop to its segment index
    const segmentIndices = planningResult.detailed_route.map((_, idx) => {
        let segmentIndex = 0;
        for (let i = 0; i < idx; i++) {
            if (planningResult.detailed_route[i].is_transfer) {
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
};

function StopCard({ stop, segmentIndex }: StopCardProps) {
    return (
        <Box className="flex flex-col items-center w-full gap-3">
            {stop.is_transfer ? (
                <>
                    <Card.Root
                        style={{
                            borderColor: `hsl(${
                                (segmentIndex * 60) % 360
                            }, 50%, 50%)`,
                        }}
                        w="full"
                        p={0}
                    >
                        <Card.Header>
                            <Text fontWeight="bold">{stop.stop_name}</Text>
                        </Card.Header>
                        <Card.Body pt={0}>
                            <Text fontSize="sm" color="gray.600">
                                Route: {stop.route_name} -{" "}
                                {stop.is_transfer ? "Transfer" : "Direct"}
                            </Text>
                            <Text fontSize="sm" color="white.800">
                                Arrival: {stop.arrival_time}
                            </Text>
                        </Card.Body>
                    </Card.Root>
                    <BsArrowLeftRight />{" "}
                </>
            ) : null}
            <Card.Root
                style={{
                    borderColor: `hsl(${
                        (stop.is_transfer
                            ? (segmentIndex + 1) * 60
                            : segmentIndex * 60) % 360
                    }, 50%, 50%)`,
                }}
                w="full"
                p={0}
            >
                <Card.Header>
                    <Text fontWeight="bold">{stop.stop_name}</Text>
                </Card.Header>
                <Card.Body pt={0}>
                    <Text fontSize="sm" color="gray.600">
                        Route: {stop.route_name} -{" "}
                        {stop.is_transfer ? "Transfer" : "Direct"}
                    </Text>
                    <Text fontSize="sm" color="white.800">
                        {stop.is_transfer
                            ? null
                            : `Arrival: ${stop.arrival_time} | `}
                        Departure: {stop.departure_time}{" "}
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
