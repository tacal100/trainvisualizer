"use client";
import { PlanningResult } from "@/app/page";
import { Badge, Box, Card, HStack, Text, VStack } from "@chakra-ui/react";

export default function ResultsBox({
    planningResult,
}: {
    planningResult: PlanningResult;
}) {
    return (
        <Box className="flex flex-col" minH={0}>
            <Text fontWeight="semibold" mb={3}>
                Journey Options
            </Text>
            <VStack gap={4} overflow={"auto"}>
                {planningResult.journeys.map((journey, idx) => (
                    <Card.Root
                        key={idx}
                        w="full"
                        bg="gray.800"
                        borderColor="gray.900"
                    >
                        <Card.Header p={2}>
                            <HStack justify="space-between">
                                <Badge>{journey.duration} min</Badge>
                                {journey.transfers > 0 && (
                                    <Badge colorScheme="orange">
                                        {journey.transfers} transfer
                                        {journey.transfers > 1 ? "s" : ""}
                                    </Badge>
                                )}
                            </HStack>
                        </Card.Header>
                        <Card.Body p={1.5} pt={0}>
                            <VStack align="stretch" gap={2}>
                                {journey.segments.map((seg, segIdx) => (
                                    <Card.Root p={0} key={segIdx} bg="gray.700">
                                        <Card.Body p={0} m={2}>
                                            <HStack gap={2}>
                                                <Box
                                                    w={2}
                                                    h={2}
                                                    borderRadius="full"
                                                    bg={seg.routeColor}
                                                />
                                                <Text
                                                    fontWeight="medium"
                                                    color="blue.400"
                                                >
                                                    {seg.route}
                                                </Text>
                                            </HStack>
                                            <Text fontSize="sm">
                                                {seg.from} → {seg.to}
                                            </Text>
                                            <Text
                                                fontSize="sm"
                                                color="gray.400"
                                            >
                                                {seg.departure} - {seg.arrival}
                                            </Text>
                                        </Card.Body>
                                    </Card.Root>
                                ))}
                            </VStack>
                        </Card.Body>
                    </Card.Root>
                ))}
            </VStack>
        </Box>
    );
}
