from typing import List, Dict, Tuple, Iterable
try:
    from racelogic.duration import Duration
except ImportError:
    from duration import Duration

from pathlib import Path

import datetime
import json


DB_DATE_FORMAT = "%y%m%d"
RESULT_FOLDER_PATH = Path.home() / "RCBashResults"
# this is necessary in production
if Path("/home/malcolm/RCBashResults").exists():
    RESULT_FOLDER_PATH = Path("/home/malcolm/RCBashResults")


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
    database = None
    with open(RESULT_FOLDER_PATH / filename) as f:
        database = json.load(f)
    return _replace_with_durations(database)


def save_database(database):
    filename = get_todays_filename()
    with open(RESULT_FOLDER_PATH / filename, "w") as f:
        json.dump(database, f, indent=2, default=lambda d: d.__dict__)


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
