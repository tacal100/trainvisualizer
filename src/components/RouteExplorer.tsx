import {
    Badge,
    Box,
    Card,
    createListCollection,
    HStack,
    Icon,
    Portal,
    Select,
    Text,
} from "@chakra-ui/react";
import { Dispatch, SetStateAction } from "react";
import { FaTrain } from "react-icons/fa";
import { Route } from "./utility/QueryService";

type RouteExplorerProps = {
    routes: Route[];
    selectedRoute: Route | null;
    setSelectedRoute: Dispatch<SetStateAction<Route | null>>;
    selectedStops: string[];
};

export default function RouteExplorer({
    routes,
    selectedRoute,
    setSelectedRoute,
    selectedStops,
}: RouteExplorerProps) {
    const routeCollection = createListCollection({
        items: routes.map((route) => ({
            label: `${route.route_short_name} - ${route.route_long_name}`,
            value: route.route_id,
            route,
        })),
    });

    return (
        <Card.Root flex={0}>
            <Card.Header>
                <Card.Title className="flex items-center" gap={2}>
                    <Icon>
                        <FaTrain />
                    </Icon>
                    <Text>Route Explorer</Text>
                </Card.Title>
            </Card.Header>
            <Card.Body>
                <Select.Root
                    collection={routeCollection.append({
                        label: "- None -",
                        value: "",
                        route: {
                            route_id: "",
                            route_short_name: "",
                            route_long_name: "",
                            route_color: "",
                        },
                    })}
                    value={[selectedRoute?.route_id || ""]}
                    onValueChange={(e) => {
                        console.log(e);
                        const route = routes.find(
                            (r) => r.route_id === e.value[0]
                        );
                        setSelectedRoute(route || null);
                    }}
                >
                    <Select.Control>
                        <Select.Trigger>
                            <Select.ValueText placeholder="Select a route to visualize" />
                        </Select.Trigger>
                    </Select.Control>
                    <Portal>
                        <Select.Positioner>
                            <Select.Content>
                                {routeCollection.items.map((item) => (
                                    <Select.Item key={item.value} item={item}>
                                        <HStack>
                                            <Box
                                                w={3}
                                                h={3}
                                                borderRadius="full"
                                                bg={item.route.route_color}
                                            />
                                            <Text>{item.label}</Text>
                                        </HStack>
                                    </Select.Item>
                                ))}
                                <Select.Item
                                    key={"none"}
                                    item={{
                                        label: "- None -",
                                        value: "",
                                        route: {
                                            route_id: "",
                                            route_short_name: "",
                                            route_long_name: "",
                                            route_color: "",
                                        },
                                    }}
                                >
                                    <HStack>
                                        <Box w={3} h={3} borderRadius="full" />
                                        <Text>- None -</Text>
                                    </HStack>
                                </Select.Item>
                            </Select.Content>
                        </Select.Positioner>
                    </Portal>
                </Select.Root>

                {selectedRoute && (
                    <Box mt={4}>
                        <Badge colorScheme="blue" mb={2}>
                            {selectedStops.length} stops
                        </Badge>
                        <Text fontSize="sm" color="gray.600">
                            Route Type: {selectedRoute.route_type}
                        </Text>
                    </Box>
                )}
            </Card.Body>
        </Card.Root>
    );
}
