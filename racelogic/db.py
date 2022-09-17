from typing import List, Dict, Tuple, Iterable, Any

try:
    from racelogic.duration import Duration
    import racelogic.names as names
except ImportError:
    from duration import Duration
    import names

from pathlib import Path

import datetime
import json

DB_DATE_FORMAT = "%y%m%d"
RESULT_FOLDER_PATH = Path.home() / "RCBashResults"
# this is necessary in production
if Path("/home/malcolm/RCBashResults").exists():
    RESULT_FOLDER_PATH = Path("/home/malcolm/RCBashResults")

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
        self.name: str = names.NAMES[number]

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

    def get_start_list(self, group: str):
        return self._start_lists[group]

    def get_groups(self) -> List[str]:
        return list(self._start_lists.keys())

    def get_serializable(self, group) -> List:
        return [d.number for d in self._start_lists[group]]

    def get_start_lists(self) -> Iterable[Tuple[str, List[Driver]]]:
        return ((group, start_list) for group, start_list in self._start_lists.items())

    def _parse_json_dict(self, json_dict: Dict) -> Dict:
        return {
            group: number_list_to_driver_list(start_list)
            for group, start_list in json_dict.items()
        }


class RaceResults:

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

    def _parse_positions(self, positions: List[int]) -> List[Driver]:
        return number_list_to_driver_list(positions)

    def _parse_dict(self, collection: Dict[int, Any]) -> Dict[Driver, Any]:
        return {Driver(int(num)): val for num, val in collection.items()}

    def _parse_time_list(self, collection: List[Tuple[int, Duration]]) -> List[Tuple[Driver, Duration]]:
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

    def get_serializable(self) -> Dict:
        results_json = {
            "positions": [d.number for d in self.positions],
            "num_laps_driven": {d.number: num_laps
                                for d, num_laps in self.num_laps_driven.items()},
            "total_times": {d.number: {"milliseconds": duration.milliseconds}
                            for d, duration in self.total_times.items()},
            "best_laptimes": [(d.number, {"milliseconds": duration.milliseconds})
                              for d, duration in self.best_laptimes],
            "average_laptimes": [(d.number, {"milliseconds": duration.milliseconds})
                                 for d, duration in self.average_laptimes],
            "manual": self.manual
        }
        if self.dns:
            results_json["dns"] = [d.number for d in self.dns]
        return results_json

    def add_dns(self, driver: Driver) -> None:
        self.dns.append(driver)


class Database:

    def __init__(self, json_db: Dict = None):
        self.all_participants: List[Driver] = \
            number_list_to_driver_list(json_db[ALL_PARTICIPANTS_KEY]) \
            if json_db is not None else []
        self.start_lists: Dict[str, Dict[str, HeatStartLists]] = \
            self._parse_start_lists(json_db[START_LISTS_KEY]) \
            if json_db is not None else {}
        self.results: Dict[str, Dict[str, Dict[str, RaceResults]]] = \
            self._parse_results(json_db[RESULTS_KEY]) \
            if json_db is not None else {}
        self.current_heat: int = json_db[CURRENT_HEAT_KEY] \
            if json_db is not None else 0

    def set_all_participants(self, number_list: List[int]) -> None:
        self.all_participants = number_list_to_driver_list(number_list)

    def set_first_qualifiers(self, participants: Dict[str, Dict[str, List]]) -> None:
        self.start_lists[QUALIFIERS_NAME] = {
            rcclass: HeatStartLists(participants[rcclass], QUALIFIERS_NAME, rcclass)
            for rcclass in participants
        }

    def save(self) -> None:
        filename = get_todays_filename()
        self._write_database(filename)

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
        race_results = RaceResults(
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

    def get_result(self, heat_name: str, rcclass: str, group: str) -> RaceResults:
        return self.results[heat_name][rcclass][group]

    def get_groups_in_race(self, heat_name: str, rcclass: str) -> List[str]:
        return self.start_lists[heat_name][rcclass].get_groups()

    def _update_start_lists_for_finals(self):
        for rcclass in ("2WD", "4WD"):
            class_results = self.results[FINALS_NAME][rcclass]
            groups = ("C", "B", "A")
            for i in range(len(groups) - 1):
                group = groups[i]
                if group in class_results:
                    group_winner = class_results[group]["positions"][0]
                    higher_group = groups[i + 1]
                    higher_group_start_list = self.start_lists[FINALS_NAME][rcclass][higher_group]
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

    def _write_database(self, filename: str) -> None:
        json_db = self._get_serializeable_db()
        with open(RESULT_FOLDER_PATH / filename, "w") as f:
            json.dump(json_db, f, indent=2, default=lambda d: d.__dict__)

    def _get_serializeable_db(self) -> Dict[str, Dict[str, Dict[str, Dict]]]:
        database = {
            ALL_PARTICIPANTS_KEY: [d.number for d in self.all_participants],
            START_LISTS_KEY: {
                heat_name: {
                    rcclass: {
                        group: group_start_list.get_serializable(group)
                        for group in group_start_list.get_groups()
                    }
                    for rcclass, group_start_list in self.start_lists[heat_name].items()
                }
                for heat_name in self.start_lists
            },
            RESULTS_KEY: {
                heat_name: {
                    rcclass: {
                        group: group_results[group].get_serializable()
                        for group in group_results
                    }
                    for rcclass, group_results in self.results[heat_name].items()
                }
                for heat_name in self.results
            },
            CURRENT_HEAT_KEY: self.current_heat
        }
        return database

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
            -> Dict[str, Dict[str, Dict[str, RaceResults]]]:
        return {
            heat_name: {
                rcclass: {
                    group_name: RaceResults(heat_name, rcclass, group_name,
                                            **json_dict[heat_name][rcclass][group_name])
                    for group_name in group_results
                }
                for rcclass, group_results in heat_results.items()
            }
            for heat_name, heat_results in json_dict.items()
        }


def number_list_to_driver_list(numbers: List[int]) -> List[Driver]:
    return [Driver(number) for number in numbers]


def create_empty_database() -> Database:
    """Creates and returns an empty Database object"""
    return Database(None)


def init_db_path() -> bool:
    """Creates DB directory and returns whether today's database already exists"""
    RESULT_FOLDER_PATH.mkdir(exist_ok=True)
    filename = get_todays_filename()
    path = RESULT_FOLDER_PATH / filename

    path_exists = path.exists()
    return path_exists


def get_all_results(date: str) -> Dict[Tuple[str, str, str], RaceResults]:
    database = get_database_with_date(date, convert_to_durations=True)
    results = {(race, rcclass, group):
                   RaceResults(race, rcclass, group,
                               **database[RESULTS_KEY][race][rcclass][group])
               for race in database[RESULTS_KEY]
               for rcclass in ("2WD", "4WD")
               for group in database[RESULTS_KEY][race][rcclass]}
    return results


def get_result(date: str, heat_name: str, rcclass: str, group: str) -> RaceResults:
    database = get_database_with_date(date, convert_to_durations=True)
    raw_results = database[RESULTS_KEY].get(heat_name, {}).get(rcclass, {}).get(group, None)
    if raw_results is None:
        return None
    return RaceResults(heat_name, rcclass, group, **raw_results)


def get_all_dates() -> List[str]:
    all_files = sorted(RESULT_FOLDER_PATH.glob("??????.json"), reverse=True)
    names = []
    for filename in all_files:
        raw_date = filename.stem
        date = datetime.datetime.strptime(raw_date, DB_DATE_FORMAT).strftime("%Y-%m-%d")
        names.append(date)
    return names


def get_todays_filename() -> str:
    todays_date = datetime.datetime.now()
    todays_date_string = todays_date.strftime(DB_DATE_FORMAT)
    return todays_date_string + ".json"


def get_database() -> Database:
    filename = get_todays_filename()
    json_db = _load_database(filename)
    return Database(json_db)


def _load_database(filename, convert_to_durations=False) -> Dict:
    with open(RESULT_FOLDER_PATH / filename) as f:
        database = json.load(f)
    return _replace_with_durations(database) if convert_to_durations else database


def get_database_with_date(date: str, convert_to_durations=False) -> Dict:
    # yeah this may not be the best design, to convert back and forth...
    db_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime(DB_DATE_FORMAT)
    filename = f"{db_date}.json"
    database = None
    with open(RESULT_FOLDER_PATH / filename) as f:
        database = json.load(f)
    return _replace_with_durations(database) if convert_to_durations else database


def _replace_with_durations(database):
    if isinstance(database, dict):
        if len(database) == 1 and "milliseconds" in database:
            return Duration(database["milliseconds"])
        else:
            replaced = {}
            for key, value in database.items():
                new_key = key
                if isinstance(key, str) and key.isnumeric():
                    new_key = int(key)

                replaced[new_key] = _replace_with_durations(value)
            return replaced
    elif isinstance(database, list):
        return [_replace_with_durations(element) for element in database]
    else:
        return database
