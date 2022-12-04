from typing import List, Dict, Tuple, Iterable, Any, Optional

from server.racelogic.duration import Duration
from .constants import RESULT_FOLDER_PATH
from ..models import get_driver_name

import datetime
import json

DB_DATE_FORMAT = "%y%m%d"

ALL_PARTICIPANTS_KEY = "all_participants"
START_LISTS_KEY = "start_lists"
RESULTS_KEY = "results"
CURRENT_HEAT_KEY = "current_heat"

QUALIFIERS_NAME = "Kval"
EIGHTH_FINAL_NAME = "Åttondelsfinal"
QUARTER_FINAL_NAME = "Kvartsfinal"
SEMI_FINAL_NAME = "Semifinal"
FINALS_NAME = "Final"

RACE_ORDER = [
    QUALIFIERS_NAME,
    EIGHTH_FINAL_NAME,
    QUARTER_FINAL_NAME,
    SEMI_FINAL_NAME,
    FINALS_NAME,
]
NON_QUALIFIER_RACE_ORDER = [
    EIGHTH_FINAL_NAME,
    QUARTER_FINAL_NAME,
    SEMI_FINAL_NAME,
    FINALS_NAME,
]
CLASS_ORDER_DEFAULT = [
    ("2WD", "C"),
    ("2WD", "B"),
    ("2WD", "A"),
    ("4WD", "C"),
    ("4WD", "B"),
    ("4WD", "A")
]
CLASS_ORDER_FINALS = [
    ("2WD", "C"),
    ("4WD", "C"),
    ("2WD", "B"),
    ("4WD", "B"),
    ("2WD", "A"),
    ("4WD", "A")
]
CLASS_ORDER = {
    QUALIFIERS_NAME: CLASS_ORDER_DEFAULT,
    EIGHTH_FINAL_NAME: CLASS_ORDER_DEFAULT,
    QUARTER_FINAL_NAME: CLASS_ORDER_DEFAULT,
    SEMI_FINAL_NAME: CLASS_ORDER_DEFAULT,
    FINALS_NAME: CLASS_ORDER_FINALS,
}


class Driver:

    def __init__(self, number: int):
        self.number: int = number
        # TODO is this inefficient?
        self.name: str = get_driver_name(number)

    def __hash__(self):
        return hash(self.number)

    def __eq__(self, other) -> bool:
        return self.number == other.number

    def __repr__(self):
        return f"Driver({self.number})"

    def __str__(self):
        return f"{self.number} {self.name}"


class HeatStartLists:

    def __init__(self, json_dict: Dict, heat_name: str, rcclass: str):
        self.heat_name: str = heat_name
        self.rcclass: str = rcclass
        self._start_lists: Dict[str, List[Driver]] = \
            self._parse_json_dict(json_dict)

    def get_start_list(self, group: str) -> List[Driver]:
        return self._start_lists[group]

    def get_groups(self) -> List[str]:
        return list(self._start_lists.keys())

    def has_group(self, group: str) -> bool:
        return group in self._start_lists

    def get_serializable(self, group) -> List:
        return [d.number for d in self._start_lists[group]]

    def get_start_lists(self) -> Iterable[Tuple[str, List[Driver]]]:
        return ((group, start_list) for group, start_list in self._start_lists.items())

    @staticmethod
    def _parse_json_dict(json_dict: Dict) -> Dict:
        return {
            group: number_list_to_driver_list(start_list) if isinstance(start_list[0], int) else start_list
            for group, start_list in json_dict.items()
        }


class RaceResult:

    def __init__(self,
                 heat_name: str,
                 rcclass: str,
                 group: str,
                 *,
                 positions: List[int],
                 num_laps_driven: Dict[int, int],
                 total_times: Dict[int, Duration],
                 best_laptimes: List[Tuple[int, Duration]],
                 average_laptimes: List[Tuple[int, Duration]],
                 manual: bool,
                 dns: List[int] = None,
                 **kwargs):
        self.heat_name: str = heat_name
        self.rcclass: str = rcclass
        self.group: str = group
        self.positions: List[Driver] = self._parse_positions(positions)
        self.num_laps_driven: Dict[Driver, int] = self._parse_dict(num_laps_driven)
        self.total_times: Dict[Driver, Duration] = self._parse_dict(total_times)
        self.best_laptimes: List[Tuple[Driver, Duration]] = self._parse_time_list(best_laptimes)
        self.average_laptimes: List[Tuple[Driver, Duration]] = self._parse_time_list(average_laptimes)
        self.manual: bool = manual
        self.dns: List[Driver] = []
        if dns is not None:
            self.dns = number_list_to_driver_list(dns)
        self.very_best_laptime: Duration = best_laptimes[0][1] if best_laptimes else None

    @staticmethod
    def _parse_positions(positions: List[int]) -> List[Driver]:
        return number_list_to_driver_list(positions)

    @staticmethod
    def _parse_dict(collection: Dict[int, Any]) -> Dict[Driver, Any]:
        return {Driver(int(num)): val for num, val in collection.items()}

    @staticmethod
    def _parse_time_list(collection: List[Tuple[int, Duration]]) -> List[Tuple[Driver, Duration]]:
        return [(Driver(num), duration) for num, duration in collection]

    def best_laptimes_dict(self):
        return {num: time for num, time in self.best_laptimes}

    def has_dns(self) -> bool:
        return len(self.dns) > 0

    def average_laptimes_dict(self):
        return {num: time for num, time in self.average_laptimes}

    def has_best_laptime(self, num):
        laptimes_dict = self.best_laptimes_dict()
        if num not in laptimes_dict:
            return False
        return self.best_laptimes[0][1] == laptimes_dict[num]

    def get_serializable(self, convert_from_durations=True) -> Dict:
        def maybe_to_millis_dict(duration: Duration) -> Any:
            if convert_from_durations:
                return {"milliseconds": duration.milliseconds}
            else:
                return duration

        results_json = {
            "positions": [d.number for d in self.positions],
            "num_laps_driven": {d.number: num_laps
                                for d, num_laps in self.num_laps_driven.items()},
            "total_times": {d.number: maybe_to_millis_dict(duration)
                            for d, duration in self.total_times.items()},
            "best_laptimes": [[d.number, maybe_to_millis_dict(duration)]
                              for d, duration in self.best_laptimes],
            "average_laptimes": [[d.number, maybe_to_millis_dict(duration)]
                                 for d, duration in self.average_laptimes],
            "manual": self.manual
        }
        if self.dns:
            results_json["dns"] = [d.number for d in self.dns]
        return results_json

    def add_dns(self, driver: Driver) -> None:
        self.dns.append(driver)

    def did_driver_start(self, driver: Driver) -> bool:
        return driver not in self.dns

    def was_manually_entered(self) -> bool:
        return self.manual

    def driver_drove_any_laps(self, driver: Driver) -> bool:
        return self.num_laps_driven.get(driver, 0) > 0


class Raceday:

    def __init__(self, json_raceday: Dict = None):
        self.all_participants: List[Driver] = \
            number_list_to_driver_list(json_raceday[ALL_PARTICIPANTS_KEY]) \
            if json_raceday is not None else []
        self.start_lists: Dict[str, Dict[str, HeatStartLists]] = \
            self._parse_start_lists(json_raceday[START_LISTS_KEY]) \
            if json_raceday is not None else {}
        self.results: Dict[str, Dict[str, Dict[str, RaceResult]]] = \
            self._parse_results(json_raceday[RESULTS_KEY]) \
            if json_raceday is not None else {}
        self.current_heat: int = json_raceday[CURRENT_HEAT_KEY] \
            if json_raceday is not None else 0

    def set_all_participants(self, number_list: List[int]) -> None:
        self.all_participants = number_list_to_driver_list(number_list)

    def set_first_qualifiers(self, participants: Dict[str, Dict[str, List]]) -> None:
        self.start_lists[QUALIFIERS_NAME] = {
            rcclass: HeatStartLists(participants[rcclass], QUALIFIERS_NAME, rcclass)
            for rcclass in participants
        }

    def save(self) -> None:
        filename = get_todays_filename()
        self._write_raceday(filename)

    def get_current_heat(self) -> str:
        return RACE_ORDER[self.current_heat]

    def get_previous_heat(self) -> str:
        return RACE_ORDER[self.current_heat - 1]

    def find_relevant_race(self, race_participants: List[Driver]) -> Tuple[str, str, str, List[Driver]]:
        race = self.get_current_heat()
        largest_match_size = 0
        largest_match_group = (None, None, None, None)
        for rcclass in self.start_lists[race]:
            for group, start_list in self.start_lists[race][rcclass].get_start_lists():
                intersection_size = len(set(race_participants).intersection(set(start_list)))
                if intersection_size > largest_match_size:
                    largest_match_size = intersection_size
                    largest_match_group = (race, rcclass, group, start_list)
        return largest_match_group

    def has_heat(self, heat_name: str) -> bool:
        return heat_name in self.results

    def add_empty_heat(self, heat_name: str) -> None:
        self.results[heat_name] = {"2WD": {}, "4WD": {}}

    def result_exists(self, heat_name: str, rcclass: str, group: str) -> bool:
        if not self.has_heat(heat_name):
            return False
        return group in self.results[heat_name][rcclass]

    def add_result(self, heat_name: str, rcclass: str, group: str,
                   positions: List[int], num_laps_driven: Dict[int, int],
                   total_times: Dict[int, Duration],
                   best_laptimes: List[Tuple[int, Duration]],
                   average_laptimes: List[Tuple[int, Duration]],
                   manual: bool,
                   start_list: List[Driver]) -> None:
        race_results = RaceResult(
            heat_name,
            rcclass,
            group,
            positions=positions,
            num_laps_driven=num_laps_driven,
            total_times=total_times,
            best_laptimes=best_laptimes,
            average_laptimes=average_laptimes,
            manual=manual
        )
        if not self.has_heat(heat_name):
            self.add_empty_heat(heat_name)
        self.results[heat_name][rcclass][group] = race_results
        self._add_dns_participants(heat_name, rcclass, group, start_list)
        if self.get_current_heat() == FINALS_NAME:
            self._update_start_lists_for_finals()

    def get_result(self, heat_name: str, rcclass: str, group: str) -> RaceResult:
        return self.results[heat_name][rcclass][group]

    def get_groups_in_race(self, heat_name: str, rcclass: str) -> List[str]:
        return self.start_lists[heat_name][rcclass].get_groups()

    def get_heat_results(self, heat_name: str) -> Optional[Dict[str, Dict[str, RaceResult]]]:
        """
        Gets all results for a particular heat. Returns None if it doesn't exist.
        Returns {"4WD": {<group>: RaceResult}, "2WD": {...}}
        """
        return self.results.get(heat_name)

    def get_current_groups(self) -> Dict[str, List[str]]:
        """
        Gets the groups in the current heat by class.
        Returns a dictionary where each class is mapped to a list of the groups.
        """
        current_heat = self.get_current_heat()
        return {
            "2WD": self.start_lists[current_heat]["2WD"].get_groups(),
            "4WD": self.start_lists[current_heat]["4WD"].get_groups(),
        }

    def get_start_lists_for_heat(self, heat_name: str) -> Dict[str, HeatStartLists]:
        """
        Gets the start lists with this heat name. Returns a dictionary:
        { "4WD": HeatStartLists, "2WD": HeatStartLists }
        """
        return self.start_lists[heat_name]

    def get_start_lists_dict(self):
        return {
            heat_name: {
                rcclass: {
                    group: group_start_list.get_serializable(group)
                    for group in group_start_list.get_groups()
                }
                for rcclass, group_start_list in self.start_lists[heat_name].items()
            }
            for heat_name in self.start_lists
        }

    def get_results_dict(self, convert_from_durations=True):
        return {
            heat_name: {
                rcclass: {
                    group: group_results[group].get_serializable(convert_from_durations)
                    for group in group_results
                }
                for rcclass, group_results in self.results[heat_name].items()
            }
            for heat_name in self.results
        }

    def are_all_races_in_round_completed(self, heat_name: str) -> bool:
        """
        Returns whether all races in a heat has a result, and we are thus
        ready to start the next round.
        """
        if not self.has_heat(heat_name):
            return False

        for rcclass in self.start_lists[heat_name]:
            for group in self.get_groups_in_race(heat_name, rcclass):
                if not self.heat_has_result(heat_name):
                    return False
                if not self.group_has_result(heat_name, rcclass, group):
                    return False
        return True

    def heat_has_result(self, heat_name: str) -> bool:
        return heat_name in self.results

    def group_has_result(self, heat_name: str, rcclass: str, group: str) -> bool:
        return group in self.results[heat_name][rcclass]

    def get_class_results(self, heat_name: str, rcclass: str) -> Dict[str, RaceResult]:
        """
        Gets the results for each class.
        Returns a dictionary where each group is mapped to its result.
        """
        return self.results[heat_name][rcclass]

    def get_all_results(self) -> Dict[Tuple[str, str, str], RaceResult]:
        """
        Returns a dictionary where (heat_name, rcclass, group) is mapped to
        each RaceResult.
        """
        results = {(heat_name, rcclass, group): self.get_result(heat_name, rcclass, group)
                   for heat_name in self.results
                   for rcclass in ("2WD", "4WD")
                   for group in self.get_groups_in_race(heat_name, rcclass)}
        return results

    def get_heats_with_results(self) -> List[str]:
        return list(self.results.keys())

    def increment_current_heat(self) -> None:
        self.current_heat += 1

    def set_new_start_lists(self, heat_name: str, raw_start_lists: Dict[str, Dict[str, List[Driver]]]) -> None:
        """Sets the start lists from a dictionary with classes mapped to groups and lists of drivers."""
        if heat_name not in self.start_lists:
            self.start_lists[heat_name] = {}
        for rcclass in raw_start_lists:
            self.start_lists[heat_name][rcclass] = HeatStartLists(raw_start_lists[rcclass], heat_name, rcclass)

    def get_latest_race_class_group(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        heat_name = self.get_current_heat()
        class_order = CLASS_ORDER[heat_name]
        heat_results = self.get_heat_results(heat_name)
        if heat_results is None:
            previous_heat = self.get_previous_heat()
            heat_results = self.results.get(previous_heat)
            if heat_results is None:
                return None, None, None

        for rcclass, group in reversed(class_order):
            class_results = heat_results[rcclass]
            if group in class_results:
                return heat_name, rcclass, group

        return None, None, None

    def _update_start_lists_for_finals(self):
        for rcclass in ("2WD", "4WD"):
            class_results = self.results[FINALS_NAME][rcclass]
            groups = ("C", "B", "A")
            for i in range(len(groups) - 1):
                group = groups[i]
                if group in class_results:
                    group_winner = class_results[group].positions[0]
                    higher_group = groups[i + 1]
                    higher_group_start_list = self.start_lists[FINALS_NAME][rcclass].get_start_list(higher_group)
                    if group_winner not in higher_group_start_list:
                        higher_group_start_list.append(group_winner)

    def _add_dns_participants(self, heat_name: str, rcclass: str,
                              group: str, start_list: List[Driver]) -> None:
        race_entry = self.results[heat_name][rcclass][group]
        positions = race_entry.positions
        not_started_participants = set(start_list) - set(positions)
        if not_started_participants:
            for driver in not_started_participants:
                race_entry.positions.append(driver)
                race_entry.add_dns(driver)

    def _write_raceday(self, filename: str) -> None:
        json_raceday = self._get_serializeable_raceday()
        with open(RESULT_FOLDER_PATH / filename, "w") as f:
            json.dump(json_raceday, f, indent=2, default=lambda d: d.__dict__)

    def _get_serializeable_raceday(self) -> Dict[str, Dict[str, Dict[str, Dict]]]:
        raceday = {
            ALL_PARTICIPANTS_KEY: [d.number for d in self.all_participants],
            START_LISTS_KEY: self.get_start_lists_dict(),
            RESULTS_KEY: self.get_results_dict(),
            CURRENT_HEAT_KEY: self.current_heat
        }
        return raceday

    def _parse_start_lists(self, json_dict: Dict[str, Dict[str, Dict[str, List]]]) -> \
            Dict[str, Dict[str, HeatStartLists]]:
        return {
            heat_name: {
                rcclass: HeatStartLists(heat_start_lists[rcclass], heat_name, rcclass)
                for rcclass in heat_start_lists
            }
            for heat_name, heat_start_lists in json_dict.items()
        }

    def _parse_results(self, json_dict: Dict[str, Dict[str, Dict[str, Dict]]])\
            -> Dict[str, Dict[str, Dict[str, RaceResult]]]:
        return {
            heat_name: {
                rcclass: {
                    group_name: RaceResult(heat_name, rcclass, group_name,
                                           **json_dict[heat_name][rcclass][group_name])
                    for group_name in group_results
                }
                for rcclass, group_results in heat_results.items()
            }
            for heat_name, heat_results in json_dict.items()
        }


def number_list_to_driver_list(numbers: List[int]) -> List[Driver]:
    return [Driver(number) for number in numbers]


def create_empty_raceday() -> Raceday:
    """Creates and returns an empty Raceday object"""
    return Raceday(None)


def init_raceday_path() -> bool:
    """Creates DB directory and returns whether today's raceday already exists"""
    RESULT_FOLDER_PATH.mkdir(exist_ok=True)
    filename = get_todays_filename()
    path = RESULT_FOLDER_PATH / filename

    path_exists = path.exists()
    return path_exists


def get_all_dates() -> List[str]:
    all_files = sorted(RESULT_FOLDER_PATH.glob("??????.json"), reverse=True)
    dates = []
    for filename in all_files:
        raw_date = filename.stem
        date = datetime.datetime.strptime(raw_date, DB_DATE_FORMAT).strftime("%Y-%m-%d")
        dates.append(date)
    return dates


def get_todays_filename() -> str:
    todays_date = datetime.datetime.now()
    todays_date_string = todays_date.strftime(DB_DATE_FORMAT)
    return todays_date_string + ".json"


def get_raceday() -> Raceday:
    filename = get_todays_filename()
    json_raceday = _load_raceday(filename, convert_to_durations=True)
    return Raceday(json_raceday)


def load_and_deserialize_raceday(filepath: str) -> Raceday:
    with open(filepath) as f:
        json_raceday = json.load(f)
    replaced_with_durations = _replace_with_durations(json_raceday)
    return Raceday(replaced_with_durations)


def _load_raceday(filename, convert_to_durations=False) -> Dict:
    with open(RESULT_FOLDER_PATH / filename) as f:
        raceday = json.load(f)
    return _replace_with_durations(raceday) if convert_to_durations else raceday


def get_raceday_with_date(date: str) -> Raceday:
    # yeah, this may not be the best design, to convert back and forth...
    raceday_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime(DB_DATE_FORMAT)
    filename = f"{raceday_date}.json"
    with open(RESULT_FOLDER_PATH / filename) as f:
        json_raceday = json.load(f)
    return Raceday(_replace_with_durations(json_raceday))


def _replace_with_durations(raceday):
    if isinstance(raceday, dict):
        if len(raceday) == 1 and "milliseconds" in raceday:
            return Duration(raceday["milliseconds"])
        else:
            replaced = {}
            for key, value in raceday.items():
                new_key = key
                if isinstance(key, str) and key.isnumeric():
                    new_key = int(key)

                replaced[new_key] = _replace_with_durations(value)
            return replaced
    elif isinstance(raceday, list):
        return [_replace_with_durations(element) for element in raceday]
    else:
        return raceday
