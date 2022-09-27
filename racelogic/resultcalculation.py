from collections import defaultdict
from typing import List, Dict, Tuple, Iterable, Callable, Any, Set

try:
    from racelogic.names import NAMES
    from racelogic.duration import Duration

    import racelogic.filelocation
    import racelogic.htmlparsing as htmlparsing
    import racelogic.textmessages as textmessages
    import racelogic.util as util
    import racelogic.db as db

except ImportError:
    from names import NAMES
    from duration import Duration

    import filelocation
    import htmlparsing
    import textmessages
    import util
    import db

import math
import argparse
import clipboard
import copy

# TODO make this a parameter
MAX_NUM_PARTICIPANTS_PER_GROUP = 9

MANUALLY_ENTERED_LAPS_DRIVEN = -1


def _input(text):
    return input(text)


def start_new_race_day():
    db_exists_already = db.init_db_path()

    if db_exists_already:
        print("There is already an ongoing race day for today!")
        answered = False
        while not answered:
            ans = _input("Do you really want to overwrite it? (yes/n): ")
            if ans == "yes":
                answered = True
            elif ans == "n":
                return False

    database = db.create_empty_database()
    database.save()

    print("New race day created for today!")

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


def _enter_participant(participants, msg="Enter a participant (blank to end group): "):
    while True:
        number = _input(msg)
        if number == "":
            return None
        elif not number.isnumeric():
            print(f"{number} isn't a number.")
        elif _number_already_entered(int(number), participants):
            print(f"Number {number} has already been entered")
        elif int(number) in NAMES:
            return int(number)
        else:
            print(f"Number {number} doesn't match any driver.")


def _enter_num_laps(number):
    while True:
        num_laps = _input(f"Enter number of laps driven by {number}: ")
        if not num_laps.isnumeric():
            print(f"{num_laps} isn't a number.")
        else:
            return int(num_laps)


def _enter_total_time(number):
    while True:
        entered = _input(f"Enter total time driven by {number} (minutes:seconds:milliseconds): ")
        try:
            minutes_str, seconds_str, milliseconds_str = entered.split(":")
            return Duration(minutes=int(minutes_str),
                            seconds=int(seconds_str),
                            milliseconds=int(milliseconds_str))
        except ValueError:
            print(f"{entered} isn't a valid time format (minutes:seconds:milliseconds)")


def _confirm_yes_no(msg="Confirm?"):
    while True:
        ans = _input(f"{msg} (y/n): ")
        if ans in ("y", "n"):
            return ans == "y"


def _confirm_group_done(start_list, rcclass, group):
    print(f"This is the start list for {rcclass} {group}:")
    print("\n".join(f"{i + 1}. {num} - {NAMES[num]}" for i, num in enumerate(start_list)))

    return _confirm_yes_no()


def _remove_empty_groups(participants):
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


def add_participants() -> Dict[str, Dict[str, List]]:
    participants = {"2WD": defaultdict(list), "4WD": defaultdict(list)}

    classes = ["2WD", "4WD"]
    groups = ["A", "B", "C"]
    for rcclass in classes:
        for group in groups:
            print(f"Now entering participants for {rcclass}, group {group}")
            print("Enter the participants in the order they will start in the qualifiers.")
            print("Empty groups will not be used.")

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


def _should_get_points(group_results, number):
    if "dns" in group_results and number in group_results["dns"]:
        return False
    return (group_results["manual"] or group_results["num_laps_driven"].get(number, 0) > 0)


def _calculate_points_from_non_finals(results, points):
    for rcclass in points:
        # iterate such that we parse A group first
        current_points = 20
        for group in sorted(results[rcclass]):
            positions = results[rcclass][group]["positions"]
            for number in positions:
                if _should_get_points(results[rcclass][group], number):
                    points[rcclass][number].append(current_points)
                else:
                    points[rcclass][number].append(0)
                current_points -= 1


def _calculate_points_from_finals(results, points):
    drivers_counted = set()
    for rcclass in points:
        # iterate such that we parse A group first
        current_points = 40
        for group in sorted(results[rcclass]):
            positions = results[rcclass][group]["positions"]
            for number in positions:
                if number not in drivers_counted:
                    drivers_counted.add(number)
                    if _should_get_points(results[rcclass][group], number):
                        points[rcclass][number].append(current_points)
                    current_points -= 2


def _calculate_cup_points(database) -> Tuple[Dict, Dict]:
    points_per_race = {"2WD": defaultdict(list), "4WD": defaultdict(list)}
    for heat_name in db.RACE_ORDER:
        if database.are_all_races_in_round_completed(heat_name):
            if heat_name not in (QUALIFIERS_NAME, FINALS_NAME) and heat_name in database[RESULTS_KEY]:
                _calculate_points_from_non_finals(database[RESULTS_KEY][heat_name], points_per_race)
            elif heat_name == FINALS_NAME:
                _calculate_points_from_finals(database[RESULTS_KEY][FINALS_NAME], points_per_race)

    return {num: sum(point_list)
            for rcclass in points_per_race
            for num, point_list in points_per_race[rcclass].items()}, points_per_race


def create_qualifiers():
    started = start_new_race_day()
    if not started:
        return

    database = db.get_database()

    participants = add_participants()
    all_participants = _get_all_participants(participants)

    database.set_all_participants(all_participants)
    database.set_first_qualifiers(participants)

    database.save()


def _get_current_groups(database):
    race = database.get_current_heat()
    return {
        "2WD": list(database[START_LISTS_KEY][race]["2WD"].keys()),
        "4WD": list(database[START_LISTS_KEY][race]["4WD"].keys()),
    }


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
            entered = _input(f"Enter the lowest group for {rcclass}: ")
        groups[rcclass] = groups_to_add[entered]
    return groups


def _select_from_list(options: List[Any], message: str, element_format_fn: Callable[[Any], str] = str) -> Any:
    print(message)
    for i, option in enumerate(options):
        print(f"{i + 1}. {element_format_fn(option)}")
    ans = ""
    while not (ans.isdigit() and 1 <= int(ans) <= len(options)):
        ans = _input(f"Select option 1-{len(options)}: ")

    return options[int(ans) - 1]


def _create_almost_equal_partitions(drivers: List[db.Driver], num_partitions: int) -> List[List[db.Driver]]:
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


def _create_start_list_from_qualifiers(groups: Dict[str, List[str]], database: db.Database) \
        -> Tuple[Dict[str, Dict[str, List[db.Driver]]], Set[db.Driver]]:
    """
    Creates the new start lists based on qualifiers results.

    Returns a dictionary where each class is mapped to a dictionary,
    where each group is mapped to a list of drivers (the start list),
    as well as a set of the duplicate drivers.
    """
    start_lists = {"2WD": {}, "4WD": {}}

    def _group_sort_fn(item: Tuple[str, db.RaceResults]) -> Tuple[int, int]:
        _, results = item
        positions = results.positions
        first = positions[0]
        return results.num_laps_driven[first], -results.total_times[first].milliseconds

    added_drivers: Set[db.Driver] = set()
    duplicate_drivers: Set[db.Driver] = set()
    for rcclass in start_lists:
        # Don't know why the type checker disagree here, but this is the correct type.
        # noinspection PyTypeChecker
        class_results: List[Tuple[str, db.RaceResults]] = sorted(
            database.get_class_results(db.QUALIFIERS_NAME, rcclass).items(),
            key=_group_sort_fn,
            reverse=True
        )

        class_positions = [copy.deepcopy(results.positions) for _, results in class_results]

        all_positions: List[db.Driver] = []
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


def _create_start_list_intermediate_races(groups, database, race):
    start_lists = {"2WD": {}, "4WD": {}}
    results = database[RESULTS_KEY][race]

    for rcclass in start_lists:
        group_results = sorted(copy.deepcopy(results[rcclass]).items(), key=lambda k: k[0])

        if len(group_results) == 1:
            start_lists[rcclass]["A"] = group_results[0][1]["positions"]

        else:
            new_start_lists = {}
            for i in range(len(group_results) - 1):
                higher_group, higher_results = group_results[i]
                lower_group, lower_results = group_results[i + 1]

                higher_positions = higher_results["positions"]
                lower_positions = lower_results["positions"]

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
        number, points = item
        point_histogram = [0] * 20
        for point in points:
            point_histogram[point - 1] += 1
        return tuple([sum(points)] + list(reversed(point_histogram)))

    return sorted(points.items(), key=key_fn)


def _create_start_lists_for_finals(database):
    start_lists = {"2WD": defaultdict(list), "4WD": defaultdict(list)}
    points, points_per_race = _calculate_cup_points(database)
    semi_results = database[RESULTS_KEY][SEMI_FINAL_NAME]

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


def _create_new_start_lists(groups: Dict[str, List[str]], database: db.Database) \
        -> Tuple[Dict[str, Dict[str, List[db.Driver]]], Set[db.Driver]]:
    current_heat = database.get_current_heat()
    if current_heat == db.QUALIFIERS_NAME:
        return _create_start_list_from_qualifiers(groups, database)
    elif current_heat in (db.EIGHTH_FINAL_NAME, db.QUARTER_FINAL_NAME):
        return _create_start_list_intermediate_races(groups, database, current_heat)
    else:
        return _create_start_lists_for_finals(database)


def start_new_race_round():
    database = db.get_database()
    current_heat = database.get_current_heat()
    if not database.are_all_races_in_round_completed(current_heat):
        print("Can't start new round yet! Not all races are completed!")
        return

    groups = database.get_current_groups()

    if database.get_current_heat() == db.QUALIFIERS_NAME:
        print(f"Current groups are 2WD {', '.join(groups['2WD'])} and 4WD {', '.join(groups['4WD'])}")
        while not _confirm_yes_no("Do you want to use these groups?"):
            groups = _enter_new_groups()
            print(f"New groups are 2WD {', '.join(groups['2WD'])} and 4WD {', '.join(groups['4WD'])}")

    new_start_lists, duplicate_drivers = _create_new_start_lists(groups, database)

    database.increment_current_heat()
    database.set_new_start_lists(database.get_current_heat(), new_start_lists)

    show_current_heat_start_list(database)

    if duplicate_drivers:
        print(f"Warning: Driver(s) {', '.join(str(n) for n in duplicate_drivers)} may have been in the wrong heat.")
        if not _confirm_yes_no("Do you want to use these start lists anyway?"):
            return
    database.save()


def _get_next_race(database):
    race = database.get_current_heat()
    heat_start_lists = database[START_LISTS_KEY][race]
    current_results = database[RESULTS_KEY].get(race)
    for class_order_index, (rcclass, group) in enumerate(CLASS_ORDER[race]):
        if group not in heat_start_lists[rcclass]:
            continue
        if current_results is None or group not in current_results[rcclass]:
            return race, rcclass, group, class_order_index
    return None, None, None, None


def _read_results():
    parser = htmlparsing.RCMHtmlParser()
    html_file_contents = filelocation.find_and_read_latest_html_file()
    parser.parse_data(html_file_contents)
    return parser


def add_new_result(drivers_to_exclude=None):
    database = db.get_database()
    parser = _read_results()

    total_times = htmlparsing.get_total_times(parser)
    num_laps_driven = htmlparsing.get_num_laps_driven(parser)
    positions = htmlparsing.get_positions(total_times, num_laps_driven)
    best_laptimes = htmlparsing.get_best_laptimes(parser)
    average_laptimes = htmlparsing.get_average_laptimes(total_times, num_laps_driven)

    race_participants = db.number_list_to_driver_list(htmlparsing.get_race_participants(parser))
    race, rcclass, group, start_list = database.find_relevant_race(race_participants)

    extra_participants = set(race_participants) - set(start_list)
    if extra_participants:
        if _confirm_yes_no(f"Driver(s) {extra_participants} weren't "
                           f"supposed to be in this race. Do you want to exclude them?"):
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
        print("Couldn't match the latest result with any race!")
        print(f"Latest race had participants {race_participants}")
        return

    print(f"The latest result matches {rcclass} {group} {race}.")
    if not _confirm_yes_no():
        print("Please manually enter the result using the --manual flag")
        return

    if database.result_exists(race, rcclass, group):
        print("This race already has a previous result, which will be overwritten.")
        if not _confirm_yes_no():
            return
        elif race == db.FINALS_NAME:
            print("Please manually remove the old winner from the next start list before doing so!")
            if not _confirm_yes_no("Have you done that?"):
                return

    database.add_result(race, rcclass, group,
                        positions, num_laps_driven, total_times,
                        best_laptimes, average_laptimes, False, start_list)

    database.save()

    results_text = textmessages.get_result_text_message(database.get_result(race, rcclass, group),
                                                        rcclass, group, race)

    clipboard.copy(results_text)
    print(results_text)

    print("^^ Copied to clipboard")


def add_new_result_manually():
    # FIXME this need to be reworked, too much is duplicated
    database = db.get_database()
    race = database.get_current_heat()

    race_options = [(rcclass, group)
                    for rcclass in ("2WD", "4WD") for group in database.get_groups_in_race(race, rcclass)]
    rcclass, group = _select_from_list(
        race_options, "Select which race to enter manually.", lambda e: " ".join(e))

    if database.result_exists(race, rcclass, group):
        print("This race already has a previous result, which will be overwritten.")
        if not _confirm_yes_no():
            return
        elif race == db.FINALS_NAME:
            print("Please manually remove the old winner from the next start list before doing so!")
            if not _confirm_yes_no("Have you done that?"):
                return

    print("Enter the drivers in the order they finished.")
    positions = []
    while True:
        number = _enter_participant(positions, msg="Enter driver number (blank to end): ")
        if number is None:
            break
        positions.append(number)

    num_laps_driven = {}
    total_times = {}
    if race == db.QUALIFIERS_NAME:
        for number in positions:
            num_laps = _enter_num_laps(number)
            total_time = _enter_total_time(number)

            num_laps_driven[number] = num_laps
            total_times[number] = total_time

    race_participants = db.number_list_to_driver_list(positions)
    race, rcclass, group, start_list = database.find_relevant_race(race_participants)

    drivers_to_exclude = []
    extra_participants = set(race_participants) - set(start_list)
    if extra_participants:
        if _confirm_yes_no(f"Driver(s) {extra_participants} weren't "
                           f"supposed to be in this race. Do you want to exclude them?"):
            for driver in extra_participants:
                drivers_to_exclude.append(driver)

    for driver in drivers_to_exclude:
        if total_times:
            del total_times[driver.number]
            del num_laps_driven[driver.number]
        positions.remove(driver.number)

    database.add_result(race, rcclass, group,
                        positions, num_laps_driven, total_times,
                        [], [], True, start_list)

    database.save()

    results_text = textmessages.get_result_text_message(database.get_result(race, rcclass, group),
                                                        rcclass, group, race)

    clipboard.copy(results_text)
    print(results_text)

    print("^^ Copied to clipboard")


def _get_latest_race_class_group(database):
    race = database.get_current_heat()
    class_order = CLASS_ORDER[race]
    results = database[RESULTS_KEY]
    heat_results = results.get(race)
    if heat_results is None:
        previous_heat = database.get_previous_heat()
        heat_results = database.get(previous_heat)
        if heat_results is None:
            return None, None, None

    for rcclass, group in reversed(class_order):
        class_results = heat_results[rcclass]
        if group in class_results:
            return race, rcclass, group

    return None, None, None


def show_latest_result(select=False):
    database = db.get_database()
    if not select:
        race, rcclass, group = _get_latest_race_class_group(database)
    else:
        race_options = [(race, rcclass, group)
                        for race in database[RESULTS_KEY]
                        for rcclass in ("2WD", "4WD")
                        for group in database[RESULTS_KEY][race][rcclass]]
        race, rcclass, group = _select_from_list(
            race_options, "Select which race to display results for.", lambda e: " ".join(e))

    if race is None:
        print("There are no results yet!")
        return

    results_text = textmessages.get_result_text_message(
        database[RESULTS_KEY][race][rcclass][group], rcclass, group, race)

    clipboard.copy(results_text)
    print(results_text)

    print("^^ Copied to clipboard")


def show_current_heat_start_list(database: db.Database = None) -> None:
    if database is None:
        database = db.get_database()
    heat_name = database.get_current_heat()
    heat_start_lists = database.get_start_lists_for_heat(heat_name)

    text_message = textmessages.create_heat_start_list_text_message(
        heat_start_lists,
        db.CLASS_ORDER[heat_name],
        heat_name,
        extra_text="Vinnare i lägre grupper deltar i nästa högre grupp (ex. B -> A)"
        if heat_name == db.FINALS_NAME else "")
    clipboard.copy(text_message)
    print(text_message)

    print("^^ Copied to clipboard")


def get_all_start_lists(date) -> Tuple[Iterable[Tuple[str, List]], Dict[str, Dict]]:
    database = db.get_database_with_date(date, convert_to_durations=False)
    start_lists = []
    marshals = {}
    current_heat_index = database[CURRENT_HEAT_KEY]

    next_heat, next_rcclass, next_group, _ = _get_next_race(database)

    for heat_index in range(current_heat_index + 1):
        heat_name = db.RACE_ORDER[heat_index]

        marshals[heat_name] = {}

        heat_start_lists = []
        class_order = CLASS_ORDER[heat_name]

        # we need to reverse all of them so they are in reverse cronological order
        for race_index, (rcclass, group) in reversed(list(enumerate(class_order))):

            is_next_race = next_heat == heat_name and \
                           next_rcclass == rcclass and \
                           next_group == group

            class_list = database[START_LISTS_KEY][heat_name][rcclass]
            if group not in class_list:
                continue
            group_list = class_list[group]

            heat_start_lists.append((rcclass, group, group_list, is_next_race))

            if rcclass not in marshals[heat_name]:
                marshals[heat_name][rcclass] = {}

            previous_rcclass, previous_group = \
                util.get_previous_group_wrap_around(
                    database[START_LISTS_KEY][heat_name],
                    CLASS_ORDER[heat_name],
                    race_index
                )
            previous_start_list = \
                database[START_LISTS_KEY][heat_name][previous_rcclass][previous_group]
            marshals[heat_name][rcclass][group] = \
                (previous_rcclass, previous_group, previous_start_list)

        start_lists.append((heat_name, heat_start_lists))
    return reversed(start_lists), marshals


def show_current_points(verbose):
    database = db.get_database()
    race = database.get_current_heat()
    points, points_per_race = _calculate_cup_points(database)

    text_message = textmessages.create_points_list_text_message(points, points_per_race, race, verbose)
    clipboard.copy(text_message)
    print(text_message)

    print("^^ Copied to clipboard")


def get_current_cup_points(date) -> Tuple[Dict, Dict]:
    database = db.get_database_with_date(date, convert_to_durations=True)
    return _calculate_cup_points(database)


def show_start_message():
    database = db.get_database()
    race, rcclass, group, class_order_index = _get_next_race(database)

    if race is None:
        print("There are no more races in this heat!")
        return

    heat_start_lists = database[START_LISTS_KEY][race]

    text_message = textmessages.create_race_start_message(
        heat_start_lists, CLASS_ORDER[race], race, rcclass, group, class_order_index)

    clipboard.copy(text_message)
    print(text_message)

    print("^^ Copied to clipboard")


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
