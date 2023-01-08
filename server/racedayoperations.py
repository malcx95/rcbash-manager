from datetime import datetime
from typing import Any, Dict


class RaceDayException(Exception):

    def __init__(self, msg):
        self.msg = msg


def create_raceday_from_json(json_data: Dict[str, Any]) -> None:
    if not json_data.get("date"):
        raise RaceDayException("'date' missing from request")
    if not json_data.get("place"):
        raise RaceDayException("'place' missing from request")
    if not json_data.get("startLists"):
        raise RaceDayException("'startLists' missing from request")

    try:
        date = datetime.strptime(json_data["date"], "%Y-%m-%d")
    except ValueError:
        raise RaceDayException(f"'date' value {json_data['date']} has an invalid format")

    start_lists = json_data["startLists"]
    if not isinstance(start_lists, dict):
        raise RaceDayException("'startLists' was of an invalid format")

    for rcclass, groups in start_lists.items():
        if not isinstance(groups, dict):
            raise RaceDayException("'startLists' was of an invalid format")
        for group, start_list in groups:
            if not isinstance(start_list, list):
                raise RaceDayException("The start lists in 'startLists' were of an invalid format")
            if not start_list:
                raise RaceDayException("One or more start lists were empty")
            if not all("number" in p for p in start_list):
                raise RaceDayException("Numbers must be present in the start lists")

    # TODO du är här, skapa säsong vid behov och lägg in startlistor
