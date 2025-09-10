"use client";
import { Badge, Box, Card, Text, VStack } from "@chakra-ui/react";
import { BsArrowLeftRight } from "react-icons/bs";
import { PlanningResult } from "./utility/QueryService";

export default function ResultsBox({
    planningResult,
}: {
    planningResult: PlanningResult;
}) {
    return (
        <Box className="flex flex-col" minH={0} gap={4}>
            <div className="flex flex-row w-full justify-between items-center !border-b !pb-4">
                <Text fontWeight="semibold">Recommended Journey</Text>
                <div className="flex flex-row gap-2">
                    <Badge background="green.500" size="md">
                        <Text fontWeight="semibold">
                            {planningResult.stop_count} Stop
                            {planningResult.stop_count !== 1 ? "s" : ""}
                        </Text>
                    </Badge>
                    <Badge background="red.500" size="md">
                        <Text fontWeight="semibold">
                            {planningResult.transfers.length} Transfer
                            {planningResult.transfers.length !== 1 ? "s" : ""}
                        </Text>
                    </Badge>
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
                    <Box
                        className="flex flex-col items-center w-full gap-3"
                        key={idx}
                    >
                        {stop.is_transfer ? <BsArrowLeftRight /> : null}
                        <Card.Root w="full" p={0}>
                            <Card.Header>
                                <Text fontWeight="bold">{stop.stop_name}</Text>
                            </Card.Header>
                            <Card.Body pt={0}>
                                <Text fontSize="sm" color="gray.600">
                                    Route: {stop.route_name} -{" "}
                                    {stop.is_transfer ? "Transfer" : "Direct"}
                                </Text>
                                <Text fontSize="sm" color="white.800">
                                    Arrival: {stop.arrival_time} | Departure:{" "}
                                    {stop.departure_time}
                                </Text>
                            </Card.Body>
                        </Card.Root>
                    </Box>
                ))}
            </VStack>
        </Box>
    );
}
