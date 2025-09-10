import { JourneySearch } from "@/app/page";
import { Button, Card, Icon, Separator, VStack } from "@chakra-ui/react";
import { LuNavigation } from "react-icons/lu";
import DateTimePicker from "./DateTimePicker";
import ResultsBox from "./ResultsBox";
import StopPicker from "./StopPicker";
import { PlanningResult } from "./utility/QueryService";

type JourneyPlannerProps = {
    stops: { stop_id: string; stop_name: string }[];
    journeySearch: JourneySearch;
    setJourneySearch: React.Dispatch<React.SetStateAction<JourneySearch>>;
    handleJourneyPlan: () => void;
    isPlanning: boolean;
    planningResult: PlanningResult | null;
};

export function JourneyPlanner({
    stops,
    journeySearch,
    setJourneySearch,
    handleJourneyPlan,
    isPlanning,
    planningResult,
}: JourneyPlannerProps) {

    return (
        <Card.Root flex={1} display="flex" flexDir="column" minH={0}>
            <Card.Header>
                <Card.Title className="flex items-center gap-2">
                    <Icon>
                        <LuNavigation />
                    </Icon>
                    Journey Planner
                </Card.Title>
            </Card.Header>
            <Card.Body flex={1} display="flex" flexDir="column" minH={0}>
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
    );
}
