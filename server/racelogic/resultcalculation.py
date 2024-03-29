from collections import defaultdict
from typing import List, Dict, Tuple, Iterable, Callable, Any, Set, Optional

try:
    from server.racelogic.names import NAMES
    from server.racelogic.duration import Duration
    from server.racelogic import htmlparsing, textmessages, raceday as rd, filelocation
    import server.racelogic.util as util
    import server.racelogic.constants as constants
except ImportError:
    from names import NAMES
    from duration import Duration
    import htmlparsing
    import textmessages
    import raceday as rd
    import filelocation
    import constants
    import util

import numpy as np

import math
import argparse
import clipboard
import copy
import os
import json

SETTINGS = {
    "max_participants": 9
}

if os.path.isfile("settings.json"):
    with open("settings.json") as f:
        SETTINGS = json.load(f)


MAX_NUM_PARTICIPANTS_PER_GROUP = SETTINGS["max_participants"]


class SeasonPoints:

    def __init__(self):
        self.total_points: Dict[rd.Driver, int] = defaultdict(int)
        self.total_points_with_drop_race: Dict[rd.Driver, int] = defaultdict(int)
        self.drop_race_indices: Dict[rd.Driver, int] = defaultdict(int)
        self.points_per_race: Dict[rd.Driver, List[int]] = defaultdict(list)
        self.race_participation: Dict[rd.Driver, List[bool]] = defaultdict(list)
        self.race_locations: List[str] = []

    def num_races(self):
        return len(self.race_locations)

    def drivers_ranked_by_points_with_drop_race(self) -> List[rd.Driver]:
        return [driver
                for driver, _ in
                sorted(self.total_points_with_drop_race.items(), key=lambda item: item[1], reverse=True)
                if driver in self.total_points]


def _input(text):
    return input(text)


def start_new_race_day():
    db_exists_already = rd.init_raceday_path()

    if db_exists_already:
        print("Det finns redan en pågående deltävling för idag!")
        answered = False
        while not answered:
            ans = _input("Vill du verkligen skriva över den? (ja/n): ")
            if ans == "ja":
                answered = True
            elif ans == "n":
                return False

    raceday = rd.create_empty_raceday()
    raceday.save()

    print("Ny deltävling skapad!")

    return True


def _number_already_entered(num, participants):
    # deal with it ok I don't have much time
    if isinstance(participants, list):
        return num in participants
    else:
        for rcclass in participants:
            for start_list in participants[rcclass].values():
                if num in start_list:
                    return True
        return False


def _enter_participant(participants, msg="Skriv in en deltagare (lämna blankt för att avsluta grupp): "):
    while True:
        number = _input(msg)
        if number == "":
            return None
        elif not number.isnumeric():
            print(f"{number} är inte ett nummer.")
        elif _number_already_entered(int(number), participants):
            print(f"Nummer {number} har redan matats in")
        elif int(number) in NAMES:
            return int(number)
        else:
            print(f"Nummer {number} matchar ingen förare.")


def _enter_num_laps(number):
    while True:
        num_laps = _input(f"Skriv in antalet varv körda av {number}: ")
        if not num_laps.isnumeric():
            print(f"{num_laps} är inte ett nummer.")
        else:
            return int(num_laps)


def _enter_total_time(number):
    while True:
        entered = _input(f"Skriv in den totala tiden för {number} (minuter:sekunder:millisekunder): ")
        try:
            minutes_str, seconds_str, milliseconds_str = entered.split(":")
            return Duration(minutes=int(minutes_str),
                            seconds=int(seconds_str),
                            milliseconds=int(milliseconds_str))
        except ValueError:
            print(f"{entered} är inte ett giltigt tidsformat (minuter:sekunder:millisekunder)")


def _confirm_yes_no(msg="Bekräfta?"):
    while True:
        ans = _input(f"{msg} (j/n): ")
        if ans in ("j", "n"):
            return ans == "j"


def _confirm_group_done(start_list, rcclass, group):
    print(f"Detta är startlistan för {rcclass} {group}:")
    print("\n".join(f"{i + 1}. {num} - {NAMES[num]}" for i, num in enumerate(start_list)))

    return _confirm_yes_no()


def _remove_empty_groups(participants: Dict[str, Dict[str, List[int]]]) -> Dict[str, Dict[str, List[int]]]:
    new_participants = {}
    for rcclass, groups in participants.items():
        new_participants[rcclass] = {}
        for group, start_list in groups.items():
            if start_list:
                new_participants[rcclass][group] = start_list
    return new_participants


def _get_all_participants(participants):
    all_participants = []
    for rcclass, groups in participants.items():
        for group, start_list in groups.items():
            all_participants.extend(start_list)
    return all_participants


def add_participants() -> Dict[str, Dict[str, List[int]]]:
    participants = {"2WD": defaultdict(list), "4WD": defaultdict(list)}

    classes = ["2WD", "4WD"]
    groups = ["A", "B", "C"]
    for rcclass in classes:
        for group in groups:
            print(f"Nu matar du in deltagare för {rcclass}, grupp {group}")
            print("Skriv deltagarna in ordningen de ska starta i sitt kvalheat.")
            print("Tomma grupper kommer inte att användas.")

            group_done = False

            while not group_done:
                number = _enter_participant(participants)
                if number is None:
                    group_done = _confirm_group_done(participants[rcclass][group], rcclass, group)
                else:
                    participants[rcclass][group].append(int(number))

            # if the group was left empty, we don't need to enter the next group in the class
            if not participants[rcclass][group]:
                break
    filtered_participants = _remove_empty_groups(participants)
    return filtered_participants


def _should_get_points(group_results: rd.RaceResult, driver: rd.Driver) -> bool:
    return not (group_results.has_dns() and not group_results.did_driver_start(driver))


def _calculate_points_from_non_finals(results: Dict[str, Dict[str, rd.RaceResult]],
                                      points: Dict[str, Dict[rd.Driver, List[int]]]) -> None:
    for rcclass in points:
        # iterate such that we parse A group first
        current_points = constants.MAX_POINTS_IN_NON_FINALS
        for group in sorted(results[rcclass]):
            positions = results[rcclass][group].positions
            for driver in positions:
                if _should_get_points(results[rcclass][group], driver):
                    points[rcclass][driver].append(current_points)
                else:
                    points[rcclass][driver].append(0)
                current_points -= 1


def _calculate_points_from_finals(results: Dict[str, Dict[str, rd.RaceResult]],
                                  points: Dict[str, Dict[rd.Driver, List[int]]]) -> None:
    drivers_counted = set()
    for rcclass in points:
        # iterate such that we parse A group first
        current_points = constants.MAX_POINTS_IN_FINALS
        for group in sorted(results[rcclass]):
            positions = results[rcclass][group].positions
            for driver in positions:
                if driver not in drivers_counted:
                    drivers_counted.add(driver)
                    if _should_get_points(results[rcclass][group], driver):
                        points[rcclass][driver].append(current_points)
                    current_points -= 2


def _calculate_cup_points(raceday: rd.Raceday) -> Tuple[Dict[rd.Driver, int], Dict[str, Dict[rd.Driver, List[int]]]]:
    points_per_race = {"2WD": defaultdict(list), "4WD": defaultdict(list)}
    for heat_name in rd.RACE_ORDER:
        if raceday.are_all_races_in_round_completed(heat_name):
            if heat_name not in (rd.QUALIFIERS_NAME, rd.FINALS_NAME) and raceday.heat_has_result(heat_name):
                _calculate_points_from_non_finals(raceday.get_heat_results(heat_name), points_per_race)
            elif heat_name == rd.FINALS_NAME:
                _calculate_points_from_finals(raceday.get_heat_results(heat_name), points_per_race)

    return {num: sum(point_list)
            for rcclass in points_per_race
            for num, point_list in points_per_race[rcclass].items()}, points_per_race


def create_qualifiers():
    started = start_new_race_day()
    if not started:
        return

    raceday = rd.get_raceday()

    participants = add_participants()
    all_participants = _get_all_participants(participants)

    raceday.set_all_participants(all_participants)
    raceday.set_first_qualifiers(participants)

    raceday.save()


def _enter_new_groups() -> Dict[str, List[str]]:
    groups_to_add = {
        "A": ["A"],
        "B": ["A", "B"],
        "C": ["A", "B", "C"]  # deal with it, I'm tired
    }

    groups = {"2WD": [], "4WD": []}
    for rcclass in groups:
        entered = ""
        while entered not in ("A", "B", "C"):
            entered = _input(f"Skriv in den lägsta gruppen för {rcclass}: ")
        groups[rcclass] = groups_to_add[entered]
    return groups


def _select_from_list(options: List[Any], message: str, element_format_fn: Callable[[Any], str] = str) -> Any:
    print(message)
    for i, option in enumerate(options):
        print(f"{i + 1}. {element_format_fn(option)}")
    ans = ""
    while not (ans.isdigit() and 1 <= int(ans) <= len(options)):
        ans = _input(f"Välj alternativ 1-{len(options)}: ")

    return options[int(ans) - 1]


def _create_almost_equal_partitions(drivers: List[rd.Driver], num_partitions: int) -> List[List[rd.Driver]]:
    if len(drivers) % num_partitions == 0:
        partitions = []
        partition_size = len(drivers) // num_partitions
        for i in range(num_partitions):
            partitions.append(drivers[i * partition_size:(i + 1) * partition_size])
        return partitions
    else:
        first_partition_size = math.ceil(len(drivers) / num_partitions)
        return [drivers[:first_partition_size]] + \
               _create_almost_equal_partitions(drivers[first_partition_size:], num_partitions - 1)


def _create_start_list_from_qualifiers(groups: Dict[str, List[str]], raceday: rd.Raceday) \
        -> Tuple[Dict[str, Dict[str, List[rd.Driver]]], Set[rd.Driver]]:
    """
    Creates the new start lists based on qualifiers results.

    Returns a dictionary where each class is mapped to a dictionary,
    where each group is mapped to a list of drivers (the start list),
    as well as a set of the duplicate drivers.
    """
    start_lists = {"2WD": {}, "4WD": {}}

    def _group_sort_fn(item: Tuple[str, rd.RaceResult]) -> Tuple[int, int]:
        _, results = item
        positions = results.positions
        first = positions[0]
        return results.num_laps_driven[first], -results.total_times[first].milliseconds

    added_drivers: Set[rd.Driver] = set()
    duplicate_drivers: Set[rd.Driver] = set()
    for rcclass in start_lists:
        # Don't know why the type checker disagrees here, but this is the correct type.
        # noinspection PyTypeChecker
        class_results: List[Tuple[str, rd.RaceResult]] = sorted(
            raceday.get_class_results(rd.QUALIFIERS_NAME, rcclass).items(),
            key=_group_sort_fn,
            reverse=True
        )

        class_positions = [copy.deepcopy(results.positions) for _, results in class_results]

        all_positions: List[rd.Driver] = []
        curr_heat = 0
        while any(class_positions):
            if len(class_positions[curr_heat]):
                driver = class_positions[curr_heat].pop(0)

                if driver in added_drivers:
                    duplicate_drivers.add(driver)
                else:
                    all_positions.append(driver)
                    added_drivers.add(driver)

            curr_heat = (curr_heat + 1) % len(class_positions)

        groups_for_class = groups[rcclass]
        partitioned_positions = _create_almost_equal_partitions(all_positions, len(groups_for_class))
        for start_list, group in zip(partitioned_positions, sorted(groups_for_class)):
            start_lists[rcclass][group] = start_list
    return start_lists, duplicate_drivers


def _create_start_list_intermediate_races(raceday: rd.Raceday, heat_name: str) \
        -> Tuple[Dict[str, Dict[str, List[rd.Driver]]], Set[rd.Driver]]:
    start_lists = {"2WD": {}, "4WD": {}}
    results = raceday.get_heat_results(heat_name)

    for rcclass in start_lists:
        # noinspection PyTypeChecker
        group_results: List[Tuple[str, rd.RaceResult]] = \
            sorted(copy.deepcopy(results[rcclass]).items(), key=lambda k: k[0])

        if len(group_results) == 1:
            start_lists[rcclass]["A"] = group_results[0][1].positions

        else:
            new_start_lists = {}
            for i in range(len(group_results) - 1):
                higher_group, higher_results = group_results[i]
                lower_group, lower_results = group_results[i + 1]

                higher_positions = higher_results.positions
                lower_positions = lower_results.positions

                higher_slowest = higher_positions.pop()
                higher_second_slowest = higher_positions.pop()

                lower_fastest = lower_positions.pop(0)
                lower_second_fastest = lower_positions.pop(0)

                higher_positions.append(lower_fastest)
                higher_positions.append(lower_second_fastest)

                lower_positions.insert(0, higher_slowest)
                lower_positions.insert(0, higher_second_slowest)

                new_start_lists[higher_group] = higher_positions
                new_start_lists[lower_group] = lower_positions

            start_lists[rcclass] = new_start_lists
    return start_lists, _remove_and_return_duplicate_drivers(start_lists)


def _remove_and_return_duplicate_drivers(start_lists):
    all_duplicate_drivers = set()
    for rcclass, group_start_lists in start_lists.items():
        added_drivers = set()
        for group, start_list in group_start_lists.items():
            for driver in start_list:
                if driver in added_drivers:
                    all_duplicate_drivers.add(driver)
                else:
                    added_drivers.add(driver)
    return all_duplicate_drivers


def _sort_by_points_and_best_heats(points):
    def key_fn(item):
        number, p = item
        point_histogram = [0] * constants.MAX_POINTS_IN_NON_FINALS
        for point in p:
            point_histogram[point - 1] += 1
        return tuple([sum(p)] + list(reversed(point_histogram)))

    return sorted(points.items(), key=key_fn)


def _create_start_lists_for_finals(raceday: rd.Raceday) \
        -> Tuple[Dict[str, Dict[str, List[rd.Driver]]], Set[rd.Driver]]:
    start_lists = {"2WD": defaultdict(list), "4WD": defaultdict(list)}
    points, points_per_race = _calculate_cup_points(raceday)

    for rcclass in start_lists:
        highest_points = _sort_by_points_and_best_heats(points_per_race[rcclass])
        group_index = 0
        groups = ["A", "B", "C"]
        while highest_points:
            curr_group = groups[group_index]
            if ((len(start_lists[rcclass][curr_group]) == (MAX_NUM_PARTICIPANTS_PER_GROUP - 1)) and
                    (len(highest_points) > 1)):
                group_index += 1
            else:
                start_lists[rcclass][curr_group].append(highest_points.pop()[0])
    return start_lists, _remove_and_return_duplicate_drivers(start_lists)


def _create_new_start_lists(groups: Dict[str, List[str]], raceday: rd.Raceday) \
        -> Tuple[Dict[str, Dict[str, List[rd.Driver]]], Set[rd.Driver]]:
    current_heat = raceday.get_current_heat()
    if current_heat == rd.QUALIFIERS_NAME:
        return _create_start_list_from_qualifiers(groups, raceday)
    elif current_heat in (rd.EIGHTH_FINAL_NAME, rd.QUARTER_FINAL_NAME):
        return _create_start_list_intermediate_races(raceday, current_heat)
    else:
        return _create_start_lists_for_finals(raceday)


def start_new_race_round():
    raceday = rd.get_raceday()
    current_heat = raceday.get_current_heat()
    if not raceday.are_all_races_in_round_completed(current_heat):
        print("Kan inte starta en ny omgång än, alla heat är inte avklarade i denna omgång!")
        return

    groups = raceday.get_current_groups()

    if raceday.get_current_heat() == rd.QUALIFIERS_NAME:
        print(f"Nuvarande grupper är 2WD {', '.join(groups['2WD'])} och 4WD {', '.join(groups['4WD'])}")
        while not _confirm_yes_no("Vill du fortfarande använda dessa grupper?"):
            groups = _enter_new_groups()
            print(f"Nya grupper är 2WD {', '.join(groups['2WD'])} och 4WD {', '.join(groups['4WD'])}")

    new_start_lists, duplicate_drivers = _create_new_start_lists(groups, raceday)

    raceday.increment_current_heat()
    raceday.set_new_start_lists(raceday.get_current_heat(), new_start_lists)

    show_current_heat_start_list(raceday)

    if duplicate_drivers:
        print(f"Varning: Förare {', '.join(str(n) for n in duplicate_drivers)} kanske körde i fel heat.")
        if not _confirm_yes_no("Vill du använda dessa startlistor ändå?"):
            return
    raceday.save()


def _get_next_race(raceday: rd.Raceday) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
    heat_name = raceday.get_current_heat()
    heat_start_lists = raceday.get_start_lists_for_heat(heat_name)
    current_results = raceday.get_heat_results(heat_name)
    for class_order_index, (rcclass, group) in enumerate(rd.CLASS_ORDER[heat_name]):
        if not heat_start_lists[rcclass].has_group(group):
            continue
        if current_results is None or group not in current_results[rcclass]:
            return heat_name, rcclass, group, class_order_index
    return None, None, None, None


def _read_results():
    parser = htmlparsing.RCMHtmlParser()
    html_file_contents = filelocation.find_and_read_latest_html_file()
    parser.parse_data(html_file_contents)
    return parser


def add_new_result(drivers_to_exclude=None):
    raceday = rd.get_raceday()
    parser = _read_results()

    total_times = htmlparsing.get_total_times(parser)
    num_laps_driven = htmlparsing.get_num_laps_driven(parser)
    positions = htmlparsing.get_positions(total_times, num_laps_driven)
    best_laptimes = htmlparsing.get_best_laptimes(parser)
    average_laptimes = htmlparsing.get_average_laptimes(total_times, num_laps_driven)

    race_participants = rd.number_list_to_driver_list(htmlparsing.get_race_participants(parser))
    race, rcclass, group, start_list = raceday.find_relevant_race(race_participants)

    extra_participants = set(race_participants) - set(start_list)
    if extra_participants:
        if _confirm_yes_no(f"Förarna {extra_participants} skulle inte "
                           f"ha kört i det här racet. Vill du ta bort dem?"):
            for driver in extra_participants:
                if drivers_to_exclude is None:
                    drivers_to_exclude = []
                drivers_to_exclude.append(driver)

    if drivers_to_exclude:
        for driver in drivers_to_exclude:
            del total_times[driver.number]
            del num_laps_driven[driver.number]
            positions.remove(driver.number)
            # FIXME this doesn't work in manual mode
            best_laptimes = [(n, time) for n, time in best_laptimes if n != driver.number]
            average_laptimes = [(n, time) for n, time in average_laptimes if n != driver.number]

    if race is None:
        print("Kunde inte matcha det senaste resultatet med något race!")
        print(f"Senaste racet hade deltagarna {race_participants}")
        return

    print(f"Det senaste resultatet matchar {rcclass} {group} {race}.")
    if not _confirm_yes_no():
        print("Mata in resultatet manuellt istället.")
        return

    if raceday.result_exists(race, rcclass, group):
        print("Det här racet har redan ett resultat, som kommer att skrivas över.")
        if not _confirm_yes_no():
            return
        elif race == rd.FINALS_NAME:
            print("Ta bort vinnaren från förra heatet manuellt innan du fortsätter!")
            if not _confirm_yes_no("Har du gjort det?"):
                return

    raceday.add_result(race, rcclass, group,
                       positions, num_laps_driven, total_times,
                       best_laptimes, average_laptimes, False, start_list)

    raceday.save()

    results_text = textmessages.get_result_text_message(raceday.get_result(race, rcclass, group),
                                                        rcclass, group, race)

    clipboard.copy(results_text)
    print(results_text)

    print("^^ Kopierat till urklipp")


def add_new_result_manually():
    # FIXME this need to be reworked, too much is duplicated
    raceday = rd.get_raceday()
    race = raceday.get_current_heat()

    race_options = [(rcclass, group)
                    for rcclass in ("2WD", "4WD") for group in raceday.get_groups_in_race(race, rcclass)]
    rcclass, group = _select_from_list(
        race_options, "Välj vilket race att mata in manuellt.", lambda e: " ".join(e))

    if raceday.result_exists(race, rcclass, group):
        print("Det här racet har redan ett resultat, som kommer att skrivas över.")
        if not _confirm_yes_no():
            return
        elif race == rd.FINALS_NAME:
            print("Ta bort vinnaren från förra heatet manuellt innan du fortsätter!")
            if not _confirm_yes_no("Har du gjort det?"):
                return

    print("Mata in förarna i ordningen de slutade.")
    positions = []
    while True:
        number = _enter_participant(positions, msg="Mata in förarnummer (lämna blankt för att avsluta): ")
        if number is None:
            break
        positions.append(number)

    num_laps_driven = {}
    total_times = {}
    if race == rd.QUALIFIERS_NAME:
        for number in positions:
            num_laps = _enter_num_laps(number)
            total_time = _enter_total_time(number)

            num_laps_driven[number] = num_laps
            total_times[number] = total_time

    race_participants = rd.number_list_to_driver_list(positions)
    race, rcclass, group, start_list = raceday.find_relevant_race(race_participants)

    drivers_to_exclude = []
    extra_participants = set(race_participants) - set(start_list)
    if extra_participants:
        if _confirm_yes_no(f"Förare {extra_participants} skulle inte ha "
                           f"deltagit i detta race. Vill du ta bort dem?"):
            for driver in extra_participants:
                drivers_to_exclude.append(driver)

    for driver in drivers_to_exclude:
        if total_times:
            del total_times[driver.number]
            del num_laps_driven[driver.number]
        positions.remove(driver.number)

    raceday.add_result(race, rcclass, group,
                       positions, num_laps_driven, total_times,
                       [], [], True, start_list)

    raceday.save()

    results_text = textmessages.get_result_text_message(raceday.get_result(race, rcclass, group),
                                                        rcclass, group, race)

    clipboard.copy(results_text)
    print(results_text)

    print("^^ Kopierat till urklipp")


def show_latest_result(select=False):
    raceday = rd.get_raceday()
    if not select:
        race, rcclass, group = raceday.get_latest_race_class_group()
    else:
        race_options = [(race, rcclass, group)
                        for race in raceday.get_heats_with_results()
                        for rcclass in ("2WD", "4WD")
                        for group in raceday.get_class_results(race, rcclass)]
        race, rcclass, group = _select_from_list(
            race_options, "Välj vilket race att visa resultat för.", lambda e: " ".join(e))

    if race is None:
        print("Det finns inga resultat än!")
        return

    results_text = textmessages.get_result_text_message(
        raceday.get_result(race, rcclass, group), rcclass, group, race)

    clipboard.copy(results_text)
    print(results_text)

    print("^^ Kopierat till urklipp")


def show_current_heat_start_list(raceday: rd.Raceday = None) -> None:
    if raceday is None:
        raceday = rd.get_raceday()
    heat_name = raceday.get_current_heat()
    heat_start_lists = raceday.get_start_lists_for_heat(heat_name)

    text_message = textmessages.create_heat_start_list_text_message(
        heat_start_lists,
        rd.CLASS_ORDER[heat_name],
        heat_name,
        extra_text="Vinnare i lägre grupper deltar i nästa högre grupp (ex. B -> A)"
        if heat_name == rd.FINALS_NAME else "")
    clipboard.copy(text_message)
    print(text_message)

    print("^^ Kopierat till urklipp")


def get_all_start_lists(raceday) -> Tuple[Iterable[Tuple[str, List]], Dict[str, Dict]]:
    start_lists = []
    marshals = {}
    current_heat_index = raceday.current_heat

    next_heat, next_rcclass, next_group, _ = _get_next_race(raceday)

    for heat_index in range(current_heat_index + 1):
        heat_name = rd.RACE_ORDER[heat_index]

        marshals[heat_name] = {}

        heat_start_lists = []
        class_order = rd.CLASS_ORDER[heat_name]

        # we need to reverse all of them, so they are in reverse chronological order
        for race_index, (rcclass, group) in reversed(list(enumerate(class_order))):

            is_next_race = next_heat == heat_name and \
                           next_rcclass == rcclass and \
                           next_group == group

            class_list = raceday.get_start_lists_for_heat(heat_name)[rcclass]
            if not class_list.has_group(group):
                continue
            group_list = class_list.get_start_list(group)

            heat_start_lists.append((rcclass, group, group_list, is_next_race))

            if rcclass not in marshals[heat_name]:
                marshals[heat_name][rcclass] = {}

            previous_rcclass, previous_group = \
                util.get_previous_group_wrap_around(
                    raceday.get_start_lists_for_heat(heat_name),
                    rd.CLASS_ORDER[heat_name],
                    race_index
                )
            previous_start_list = \
                raceday.get_start_lists_for_heat(heat_name)[previous_rcclass].get_start_list(previous_group)
            marshals[heat_name][rcclass][group] = \
                (previous_rcclass, previous_group, previous_start_list)

        start_lists.append((heat_name, heat_start_lists))
    return reversed(start_lists), marshals


def _get_all_participants_over_a_season(racedays: List[rd.Raceday]) -> Set[rd.Driver]:
    all_participants = set()
    for raceday in racedays:
        all_participants.update(set(raceday.all_participants))
    return all_participants


def _delete_if_exists(key: Any, dictionary: Dict):
    if key in dictionary:
        del dictionary[key]


def _remove_drivers_with_no_participation(season_points_per_class: Dict[str, SeasonPoints]):
    drivers_to_remove = []
    for rcclass in ("2WD", "4WD"):
        season_points = season_points_per_class[rcclass]
        for driver in season_points.race_participation:
            if not any(season_points.race_participation[driver]):
                drivers_to_remove.append((rcclass, driver))

    for rcclass, driver in drivers_to_remove:
        _delete_if_exists(driver, season_points_per_class[rcclass].total_points)
        _delete_if_exists(driver, season_points_per_class[rcclass].total_points_with_drop_race)
        del season_points_per_class[rcclass].drop_race_indices[driver]
        del season_points_per_class[rcclass].points_per_race[driver]
        del season_points_per_class[rcclass].race_participation[driver]


def calculate_season_points(racedays: List[rd.Raceday], race_locations: List[str]) \
        -> Dict[str, SeasonPoints]:
    """
    Calculates the cup points over a season, and returns a dictionary where
    each rcclass is mapped to the points those drivers got.
    """
    season_points_per_class = {"2WD": SeasonPoints(), "4WD": SeasonPoints()}
    season_points_per_class["2WD"].race_locations = race_locations
    season_points_per_class["4WD"].race_locations = race_locations
    all_drivers = _get_all_participants_over_a_season(racedays)
    points_for_all_races = [_calculate_cup_points(raceday) for raceday in racedays]
    for driver in all_drivers:
        for race_points, points_per_heat in points_for_all_races:
            rcclass = "2WD" if driver in points_per_heat["2WD"] else "4WD"
            driver_points = race_points.get(driver, None)
            drove_in_neither_class = driver_points is None

            race_points = driver_points if not drove_in_neither_class else 0
            season_points_per_class[rcclass].total_points[driver] += race_points
            season_points_per_class[rcclass].total_points_with_drop_race[driver] += race_points
            season_points_per_class[rcclass].points_per_race[driver].append(race_points)
            season_points_per_class[rcclass].race_participation[driver].append(not drove_in_neither_class)

            not_rcclass = "4WD" if rcclass == "2WD" else "2WD"
            season_points_per_class[not_rcclass].points_per_race[driver].append(0)
            season_points_per_class[not_rcclass].race_participation[driver].append(False)

        for rcclass in ("2WD", "4WD"):
            drop_race_index = np.argmin(season_points_per_class[rcclass].points_per_race[driver])
            drop_race_points = season_points_per_class[rcclass].points_per_race[driver][drop_race_index]
            season_points_per_class[rcclass].drop_race_indices[driver] = int(drop_race_index)
            season_points_per_class[rcclass].total_points_with_drop_race[driver] -= drop_race_points

    _remove_drivers_with_no_participation(season_points_per_class)
    return season_points_per_class


def show_current_points(verbose):
    raceday = rd.get_raceday()
    heat_name = raceday.get_current_heat()
    points, points_per_race = _calculate_cup_points(raceday)

    text_message = textmessages.create_points_list_text_message(points, points_per_race, heat_name, verbose)
    clipboard.copy(text_message)
    print(text_message)

    print("^^ Kopierat till urklipp")


def get_current_cup_points(date) -> Tuple[Dict[rd.Driver, int], Dict[str, Dict[rd.Driver, List[int]]]]:
    raceday = rd.get_raceday_with_date(date)
    return _calculate_cup_points(raceday)


def show_start_message():
    raceday = rd.get_raceday()

    heat_name, rcclass, group, class_order_index = _get_next_race(raceday)

    if heat_name is None:
        print("Det finns inga fler race i detta heat!")
        return

    heat_start_lists = raceday.get_start_lists_for_heat(heat_name)

    text_message = textmessages.create_race_start_message(
        heat_start_lists, rd.CLASS_ORDER[heat_name], heat_name, rcclass, group, class_order_index)

    clipboard.copy(text_message)
    print(text_message)

    print("^^ Kopierat till urklipp")


def main():
    parser = argparse.ArgumentParser(description="Manages an RCBash race day.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--new-race-day", action="store_true",
                       help="Start a new race day")
    group.add_argument("-r", "--result", action="store_true",
                       help="Add new result")
    group.add_argument("-n", "--next-round", action="store_true",
                       help="Start the next round")
    group.add_argument("-d", "--show-result", action="store_true",
                       help="Display the a result as text. Use '-p'/'--select-result' flag "
                            "to select which result, if empty the latest will be shown.")
    group.add_argument("-l", "--show-heat-start-lists", action="store_true",
                       help="Show the start lists for the current heat")
    group.add_argument("-o", "--show-points", action="store_true",
                       help="Show the current points.")
    group.add_argument("-g", "--start-message", action="store_true",
                       help="Show the current race to be started.")

    parser.add_argument("-m", "--manual", action="store_true",
                        help="Add a result manually")
    parser.add_argument("-p", "--select-result", action="store_true",
                        help="Select a result manually")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show points from all heats")
    parser.add_argument("-e", "--exclude", nargs="+", type=int,
                        help="Exclude these drivers from the result and give them 0 points.")

    args = parser.parse_args()

    if args.new_race_day:
        create_qualifiers()
    elif args.result and not args.manual:
        add_new_result(args.exclude)
    elif args.result and args.manual:
        add_new_result_manually()
    elif args.next_round:
        start_new_race_round()
    elif args.show_result:
        show_latest_result(select=args.select_result)
    elif args.show_heat_start_lists:
        show_current_heat_start_list()
    elif args.show_points:
        show_current_points(args.verbose)
    elif args.start_message:
        show_start_message()


if __name__ == "__main__":
    main()
