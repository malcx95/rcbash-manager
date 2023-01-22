from typing import Dict, List, Tuple, Any

from server.racelogic.duration import Duration
from server.racelogic.raceday import HeatStartLists


def replace_durations_with_dict(object_with_durations: Any) -> Any:
    """
    Replaces all Duration objects in the given object with serializable dicts
    (by calling duration.minutest_seconds_milliseconds_dict() on all durations)
    """
    if isinstance(object_with_durations, Duration):
        return object_with_durations.minutes_seconds_milliseconds_dict()
    elif isinstance(object_with_durations, list):
        return [replace_durations_with_dict(o) for o in object_with_durations]
    elif isinstance(object_with_durations, tuple):
        return tuple(replace_durations_with_dict(o) for o in object_with_durations)
    elif isinstance(object_with_durations, set):
        return {replace_durations_with_dict(o) for o in object_with_durations}
    elif isinstance(object_with_durations, dict):
        return {k: replace_durations_with_dict(v) for k, v in object_with_durations.items()}
    else:
        return object_with_durations


def get_previous_group_wrap_around(
        heat_start_lists: Dict[str, HeatStartLists],
        race_order: List[Tuple[str, str]],
        index: int):
    temp_index = index
    while True:
        if temp_index == 0:
            temp_index = len(race_order) - 1
        else:
            temp_index -= 1
        previous_rcclass, previous_group = race_order[temp_index]

        if heat_start_lists[previous_rcclass].has_group(previous_group):
            return previous_rcclass, previous_group
