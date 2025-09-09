import { JourneySearch, Stop } from "@/app/page";
import { createListCollection, Portal, Select } from "@chakra-ui/react";
import { Dispatch, SetStateAction } from "react";

type StopPickerProps = {
    stops: Stop[];
    journeySearch: JourneySearch;
    setJourneySearch: Dispatch<SetStateAction<JourneySearch>>;
    from: boolean;
};
export default function StopPicker({
    stops,
    journeySearch,
    setJourneySearch,
    from,
}: StopPickerProps) {
    const stopCollection = createListCollection({
        items: stops.map((stop) => ({
            label: stop.stop_name,
            value: stop.stop_id,
        })),
    });

    return (
        <Select.Root
            collection={stopCollection}
            value={from ? [journeySearch.from] : [journeySearch.to]}
            onValueChange={(details) => {
                const selectedId = details.value[0];
                setJourneySearch((prev) => ({
                    ...prev,
                    [from ? "from" : "to"]: selectedId,
                }));
            }}
        >
            <Select.Control>
                <Select.Trigger>
                    <Select.ValueText
                        placeholder={from ? "From station" : "To station"}
                    />
                </Select.Trigger>
            </Select.Control>
            <Portal>
                <Select.Positioner>
                    <Select.Content>
                        {stopCollection.items.map((item) => (
                            <Select.Item key={item.value} item={item}>
                                {item.label}
                            </Select.Item>
                        ))}
                    </Select.Content>
                </Select.Positioner>
            </Portal>
        </Select.Root>
    );
}
