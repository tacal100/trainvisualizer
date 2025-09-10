"use client";
import { Box, Text, VStack } from "@chakra-ui/react";
import { PlanningResult } from "./utility/QueryService";

export default function ResultsBox({
    planningResult,
}: {
    planningResult: PlanningResult;
}) {
    return (
        <Box className="flex flex-col" minH={0}>
            <Text fontWeight="semibold" mb={3}>
                Recommended Journey
            </Text>
            <VStack gap={4} overflow={"auto"}>
                {planningResult.detailed_route.map((stop, idx) => (
                    <span key={idx}>{stop.stop_name}</span>
                ))}
            </VStack>
        </Box>
    );
}
