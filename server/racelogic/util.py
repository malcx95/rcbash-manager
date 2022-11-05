from typing import Dict, List, Tuple

try:
    from server.racelogic.raceday import HeatStartLists
except ImportError:
    from raceday import HeatStartLists


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
