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


class Driver:

    def __init__(self, number: int):
        self.number: int = number
        self.name: str = names.NAMES[number]

    def __hash__(self):
        return hash(self.number)

    def __eq__(self, other):
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

    def get_start_list(rcclass: str, group: str):
        if rcclass not in ("2WD", "4WD"):
            raise ValueError(f"Invalid rcclass {rcclass}, must be '4WD' or '2WD'.")

        class_lists = self._start_lists[rcclass]
        if group not in class_lists:
            raise ValueError(
                f"Group '{group}', does not exist in heat {rcclass} {heat_name}.")

        return class_lists[group]

    def get_groups(self) -> List[str]:
        return list(self._start_lists.keys())

    def get_serializable(self, group) -> List:
        return [d.number for d in self._start_lists[group]]

    def _parse_json_dict(self, json_dict: Dict) -> Dict:
        return {
            group: [Driver(num) for num in start_list]
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
                 dns: List[int]=None,
                 **kwargs):
        self.heat_name: str = heat_name
        self.rcclass: str = rcclass
        self.group: str = group
        self.positions: List[Driver] = self._parse_positions(positions)
        self.num_laps_driven: Dict[Driver, int] = self._parse_dict(num_laps_driven)
        self.total_times: Dict[int, Duration] = self._parse_dict(total_times)
        self.best_laptimes: List[Tuple[int, Duration]] = self._parse_time_list(best_laptimes)
        self.average_laptimes: List[Tuple[int, Duration]] = self._parse_time_list(average_laptimes)
        self.manual: bool = manual
        self.dns: List[Driver] = []
        if dns is not None:
            self.dns = [Driver(num) for num in dns]
        self.very_best_laptime: Duration = best_laptimes[0][1] if best_laptimes else None

    def _parse_positions(self, positions: List[int]) -> List[Driver]:
        return [Driver(num) for num in positions]

    def _parse_dict(self, collection: Dict[int, Any]) -> Dict[Driver, Any]:
        return {Driver(int(num)): val for num, val in collection.items()}

    def _parse_time_list(self, collection: List[Tuple[int, Duration]]) -> List[Tuple[Driver, Duration]]:
        return [(Driver(num), duration) for num, duration in collection]

    def best_laptimes_dict(self):
        return {num: time for num, time in self.best_laptimes}

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


class Database:

    def __init__(self, json_db: Dict):

        self.all_participants: List[Driver] = \
            [Driver(num) for num in json_db[ALL_PARTICIPANTS_KEY]]
        self.start_lists: Dict[str, Dict[str, HeatStartLists]] = \
            self._parse_start_lists(json_db[START_LISTS_KEY])
        self.results: Dict[str, Dict[str, RaceResults]] = \
            self._parse_results(json_db[RESULTS_KEY])
        self.current_heat: int = json_db[CURRENT_HEAT_KEY]

    def set_all_participants(self, number_list: List[int]) -> None:
        self.all_participants = [Driver(num) for num in number_list]

    def set_first_qualifiers(self, participants: Dict[str, Dict[str, List]]) -> None:
        self.start_lists[QUALIFIERS_NAME] = {
            rcclass: HeatStartLists(participants[rcclass], QUALIFIERS_NAME, rcclass)
            for rcclass in participants
        }

    def save(self) -> None:
        filename = get_todays_filename()
        self._write_database(filename)

    def _write_database(self, filename: str) -> None:
        json_db = self._get_serializeable_db()
        with open(RESULT_FOLDER_PATH / filename, "w") as f:
            json.dump(json_db, f, indent=2, default=lambda d: d.__dict__)

    def _get_serializeable_db(self) -> Dict:
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

    def _parse_start_lists(self, json_dict: Dict[str, Dict[str, List]]) -> Dict[str, Dict[str, HeatStartLists]]:
        return {
            heat_name: {
                rcclass: HeatStartLists(heat_start_lists[rcclass], heat_name, rcclass)
                for rcclass in heat_start_lists
            }
            for heat_name, heat_start_lists in json_dict.items()
        }

    def _parse_results(self, json_dict: Dict[str, Dict[str, RaceResults]]) -> Dict[str, Dict[str, RaceResults]]:
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


def get_all_results(date: str) -> Dict[Tuple[str, str, str], RaceResults]:
    database = db.get_database_with_date(date, convert_to_durations=True)
    results = {(race, rcclass, group):
               RaceResults(race, rcclass, group,
                         **database[RESULTS_KEY][race][rcclass][group])
               for race in database[RESULTS_KEY]
               for rcclass in ("2WD", "4WD")
               for group in database[RESULTS_KEY][race][rcclass]}
    return results


def get_result(date: str, heat_name: str, rcclass: str, group: str) -> RaceResults:
    database = db.get_database_with_date(date, convert_to_durations=True)
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


def get_todays_filename():
    todays_date = datetime.datetime.now()
    todays_date_string = todays_date.strftime(DB_DATE_FORMAT)
    return todays_date_string + ".json"


def get_database():
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
