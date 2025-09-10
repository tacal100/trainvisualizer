import { Box, HStack, Icon, Input, Text } from "@chakra-ui/react";
import { Dispatch, SetStateAction } from "react";
import { LuCalendar, LuClock } from "react-icons/lu";

type JourneySearch = {
    from: string;
    to: string;
    date: string;
    time: string;
};

type SetJourneySearch = Dispatch<
    SetStateAction<{
        from: string;
        to: string;
        date: string;
        time: string;
    }>
>;

type DateTimePickerProps = {
    journeySearch: JourneySearch;
    setJourneySearch: SetJourneySearch;
};

/**
 * Select for date and time of journey.
 */
export default function DateTimePicker({
    journeySearch,
    setJourneySearch,
}: DateTimePickerProps) {
    return (
        <HStack w="full">
            <Box flex={1}>
                <HStack mb={1}>
                    <Icon size="xs">
                        <LuCalendar />
                    </Icon>
                    <Text fontSize="sm">Date</Text>
                </HStack>
                <Input
                    type="date"
                    value={journeySearch.date}
                    onChange={(e) =>
                        setJourneySearch({
                            ...journeySearch,
                            date: e.target.value,
                        })
                    }
                />
            </Box>
            <Box flex={1}>
                <HStack mb={1}>
                    <Icon size="xs">
                        <LuClock />
                    </Icon>
                    <Text fontSize="sm">Time</Text>
                </HStack>
                <Input
                    type="datetime"
                    value={journeySearch.time}
                    onChange={(e) =>
                        setJourneySearch({
                            ...journeySearch,
                            time: e.target.value,
                        })
                    }
                />
            </Box>
        </HStack>
    );
}
