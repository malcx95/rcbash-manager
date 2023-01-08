from datetime import datetime
from typing import Any, Dict, List, Tuple
import server.racelogic.raceday as rd
from server import models


class RaceDayException(Exception):

    def __init__(self, msg):
        self.msg = msg


def _extract_all_participants(start_lists: Dict[str, Dict[str, List[int]]]) -> List[int]:
    all_participants = []
    for rcclass, groups in start_lists.items():
        for group, start_list in groups.items():
            all_participants.extend(start_list)
    return all_participants


def create_raceday_from_json(json_data: Dict[str, Any]) -> Tuple[int, str]:
    """
    Creates a raceday from the json form data, and saves it to the database
    and the file to disk. Also validates the form and raises a RaceDayException
    if the form is invalid.

    Returns the year and date string of the newly created raceday (YYYY-MM-DD).
    """
    if not json_data.get("date"):
        raise RaceDayException("'date' missing from request")
    if not json_data.get("location"):
        raise RaceDayException("'location' missing from request")
    if not json_data.get("startLists"):
        raise RaceDayException("'startLists' missing from request")

    date_str = json_data["date"]
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise RaceDayException(f"'date' value {json_data['date']} has an invalid format")

    start_lists = json_data["startLists"]
    if not isinstance(start_lists, dict):
        raise RaceDayException("'startLists' was of an invalid format")

    # the json start lists comes as { rcclass: { group: [ { name: ..., number: ... } ] } }
    # so we need to make sure the lists are just numbers
    processed_start_lists: Dict[str, Dict[str, List[int]]] = {}
    for rcclass, groups in start_lists.items():
        if rcclass not in processed_start_lists:
            processed_start_lists[rcclass] = {}
        if not isinstance(groups, dict):
            raise RaceDayException("'startLists' was of an invalid format")
        for group, start_list in groups.items():
            if not isinstance(start_list, list):
                raise RaceDayException("The start lists in 'startLists' were of an invalid format")
            if not start_list:
                raise RaceDayException("One or more start lists were empty")
            if not all("number" in p for p in start_list):
                raise RaceDayException("Numbers must be present in the start lists")
            processed_start_lists[rcclass][group] = [p["number"] for p in start_list]

    raceday = rd.create_empty_raceday()
    all_participants = _extract_all_participants(processed_start_lists)
    raceday.set_all_participants(all_participants)
    raceday.set_first_qualifiers(processed_start_lists)
    filename = rd.get_raceday_filename_date(date)

    raceday.save_as_date(filename)
    models.create_raceday(filename, date, json_data["location"])

    return date.year, date_str
