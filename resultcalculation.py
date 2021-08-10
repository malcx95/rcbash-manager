from pathlib import Path
from collections import defaultdict

from names import NAMES
from duration import Duration

import filelocation
import htmlparsing
import textmessages

import math
import json
import datetime
import argparse
import clipboard
import copy

MAX_NUM_PARTICIPANTS_PER_GROUP = 6

RESULT_FOLDER_PATH = Path.home() / "RCBashResults"

ALL_PARTICIPANTS_KEY = "all_participants"
START_LISTS_KEY = "start_lists"
RESULTS_KEY = "results"
CURRENT_HEAT_KEY = "current_heat"

MANUALLY_ENTERED_LAPS_DRIVEN = -1

QUALIFIERS_NAME = "qualifiers"
EIGHTH_FINAL_NAME = "1/8 final"
QUARTER_FINAL_NAME = "1/4 final"
SEMI_FINAL_NAME = "Semifinal"
FINALS_NAME = "Final"

RACE_ORDER = [
    QUALIFIERS_NAME,
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


def _get_todays_filename():
    todays_date = datetime.datetime.now()
    todays_date_string = todays_date.strftime("%y%m%d")
    return todays_date_string + ".json"


def _get_database():
    filename = _get_todays_filename()
    database = None
    with open(RESULT_FOLDER_PATH / filename) as f:
        database = json.load(f)
    return _replace_with_durations(database)


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


def _save_database(database):
    filename = _get_todays_filename()
    with open(RESULT_FOLDER_PATH / filename, "w") as f:
        json.dump(database, f, indent=2, default=lambda d: d.__dict__)


def start_new_race_day():
    RESULT_FOLDER_PATH.mkdir(exist_ok=True)
    filename = _get_todays_filename()

    path = RESULT_FOLDER_PATH / filename
    database = {
        ALL_PARTICIPANTS_KEY: {},
        START_LISTS_KEY: {},
        RESULTS_KEY: {},
        CURRENT_HEAT_KEY: 0
    }

    if path.exists():
        print("There is already an ongoing race day for today!")
        answered = False
        while not answered:
            ans = input("Do you really want to overwrite it? (yes/n): ")
            if ans == "yes":
                answered = True
            elif ans == "n":
                return False
    
    with open(path, "w") as f:
        json.dump(database, f)

    print(f"New race day created in {str(path)}!")

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
        number = input(msg)
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


def _confirm_yes_no(msg="Confirm?"):
    while True:
        ans = input(f"{msg} (y/n): ")
        if ans in ("y", "n"):
            return ans == "y"


def _confirm_group_done(start_list, rcclass, group):
    print(f"This is the start list for {rcclass} {group}:")
    print("\n".join(f"{i+1}. {num} - {NAMES[num]}" for i, num in enumerate(start_list)))

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


def add_participants():
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


def _get_current_heat(database):
    return RACE_ORDER[database[CURRENT_HEAT_KEY]]

def _get_previous_heat(database):
    return RACE_ORDER[database[CURRENT_HEAT_KEY] - 1]


def _find_relevant_race(race_participants, database):
    race = _get_current_heat(database)
    for rcclass in database[START_LISTS_KEY][race]:
        for group, start_list in database[START_LISTS_KEY][race][rcclass].items():
            if set(race_participants).issubset(set(start_list)):
                return race, rcclass, group, start_list
    return None, None, None, None


def _should_get_points(group_results):
    return results["manual"] or results["num_laps_driven"].get(number, 0) > 0


def _calculate_points_from_non_finals(results, points):
    for rcclass in points:
        # iterate such that we parse A group first
        current_points = 20
        for group in sorted(results[rcclass]):
            positions = results[rcclass][group]["positions"]
            for number in positions:
                if _should_get_points:
                    points[rcclass][number].append(current_points)
                current_points -= 1


def _calculate_cup_points(database):
    points_per_race = {"2WD": defaultdict(list), "4WD": defaultdict(list)}
    for race in RACE_ORDER:
        if race not in (QUALIFIERS_NAME, FINALS_NAME) and race in database[RESULTS_KEY]:
            _calculate_points_from_non_finals(database[RESULTS_KEY][race], points_per_race)
        # TODO add finals

    return {num: sum(point_list)
            for rcclass in points_per_race
            for num, point_list in points_per_race[rcclass].items()}, points_per_race


def create_qualifiers():
    started = start_new_race_day()
    if not started:
        return

    database = _get_database()

    participants = add_participants()
    all_participants = _get_all_participants(participants)

    database[ALL_PARTICIPANTS_KEY] = all_participants
    database[START_LISTS_KEY][QUALIFIERS_NAME] = participants

    _save_database(database)


def _are_all_races_in_current_round_completed(database):
    race = _get_current_heat(database)
    for rcclass in database[START_LISTS_KEY][race]:
        for group in database[START_LISTS_KEY][race][rcclass]:
            if race not in database[RESULTS_KEY]:
                return False
            if group not in database[RESULTS_KEY][race][rcclass]:
                return False
    return True


def _get_current_groups(database):
    race = _get_current_heat(database)
    return {
        "2WD": list(database[START_LISTS_KEY][race]["2WD"].keys()),
        "4WD": list(database[START_LISTS_KEY][race]["4WD"].keys()),
    }


def _enter_new_groups():
    groups_to_add = {
        "A": ["A"],
        "B": ["A", "B"],
        "C": ["A", "B", "C"]  # deal with it, I'm tired
    }

    groups = {"2WD": [], "4WD": []}
    for rcclass in groups:
        entered = ""
        while entered not in ("A", "B", "C"):
            entered = input(f"Enter the lowest group for {rcclass}: ")
        groups[rcclass] = groups_to_add[entered]
    return groups


def _select_from_list(options, message, element_format_fn=str):
    print(message)
    for i, option in enumerate(options):
        print(f"{i + 1}. {element_format_fn(option)}")
    ans = ""
    while not (ans.isdigit() and 1 <= int(ans) <= len(options)):
        ans = input(f"Select option 1-{len(options)}: ")
    
    return options[int(ans) - 1]


def _create_almost_equal_partitions(numbers, num_partitions):
    if len(numbers) % num_partitions == 0:
        partitions = []
        partition_size = len(numbers) // num_partitions
        for i in range(num_partitions):
            partitions.append(numbers[i*partition_size:(i+1)*partition_size])
        return partitions
    else:
        first_partition_size = math.ceil(len(numbers) / num_partitions)
        return [numbers[:first_partition_size]] + \
                _create_almost_equal_partitions(numbers[first_partition_size:], num_partitions - 1)


def _create_start_list_from_qualifiers(groups, database):
    start_lists = {"2WD": {}, "4WD": {}}
    qualifier_results = database[RESULTS_KEY][QUALIFIERS_NAME]
    
    def _group_sort_fn(item):
        group, results = item
        positions = results["positions"]
        first = positions[0]
        return (results["num_laps_driven"][first], -results["total_times"][first].milliseconds)

    for rcclass in start_lists:
        all_total_times = {}
        all_num_laps_driven = {}

        group_results = sorted(
            qualifier_results[rcclass].items(),
            key=_group_sort_fn,
            reverse=True
        )

        group_positions = [copy.deepcopy(results["positions"]) for _, results in group_results]

        all_positions = []
        curr_heat = 0
        while any(group_positions):
            if len(group_positions[curr_heat]):
                all_positions.append(group_positions[curr_heat].pop(0))
            curr_heat = (curr_heat + 1) % len(group_positions)

        groups_for_class = groups[rcclass]
        partitioned_positions = _create_almost_equal_partitions(all_positions, len(groups_for_class))
        for start_list, group in zip(partitioned_positions, sorted(groups_for_class)):
            start_lists[rcclass][group] = start_list
    return start_lists


def _create_start_list_intermediate_races(groups, database, race):
    start_lists = {"2WD": {}, "4WD": {}}
    results = database[RESULTS_KEY][race]

    for rcclass in start_lists:
        group_results = sorted(copy.deepcopy(results[rcclass]).items(), key=lambda k: k[0])

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
    return start_lists


def _sort_by_points_and_best_heats(points):

    def key_fn(item):
        number, points = item
        point_histogram = [0]*20
        for point in points:
            point_histogram[point-1] += 1
        return tuple([sum(points)] + point_histogram)

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
    return start_lists


def _create_new_start_lists(groups, database):
    race = _get_current_heat(database)
    if race == QUALIFIERS_NAME:
        return _create_start_list_from_qualifiers(groups, database)
    elif race in (EIGHTH_FINAL_NAME, QUARTER_FINAL_NAME):
        return _create_start_list_intermediate_races(groups, database, race)
    else:
        return _create_start_lists_for_finals(database)


def start_new_race_round():
    database = _get_database()
    if not _are_all_races_in_current_round_completed(database):
        print("Can't start new round yet! Not all races are completed!")
        return

    groups = _get_current_groups(database)

    if _get_current_heat(database) == QUALIFIERS_NAME:
        print(f"Current groups are 2WD {', '.join(groups['2WD'])} and 4WD {', '.join(groups['4WD'])}")
        while not _confirm_yes_no("Do you want to use these groups?"):
            groups = _enter_new_groups()
            print(f"New groups are 2WD {', '.join(groups['2WD'])} and 4WD {', '.join(groups['4WD'])}")

    new_start_lists = _create_new_start_lists(groups, database)
    current_heat = database[CURRENT_HEAT_KEY]
    current_heat += 1
    database[CURRENT_HEAT_KEY] = current_heat
    
    database[START_LISTS_KEY][RACE_ORDER[current_heat]] = new_start_lists

    print(new_start_lists)
    _save_database(database)


def _add_dns_participants(race_entry, start_list):
    positions = race_entry["positions"]
    not_started_participants = set(start_list) - set(positions)
    if not_started_participants:
        for number in not_started_participants:
            race_entry["positions"].append(number)


def _update_start_lists_for_finals(database):
    for rcclass in ("2WD", "4WD"):
        class_results = database[RESULTS_KEY][FINALS_NAME][rcclass]
        groups = ("C", "B", "A")
        for i in range(len(groups) - 1):
            group = groups[i]
            if group in class_results:
                group_winner = class_results[group]["positions"][0]
                higher_group = groups[i + 1]
                higher_group_start_list = database[START_LISTS_KEY][FINALS_NAME][rcclass][higher_group]
                if group_winner not in higher_group_start_list:
                    higher_group_start_list.append(group_winner)


def add_new_result():
    database = _get_database()
    parser = htmlparsing.RCMHtmlParser()
    html_file_contents = filelocation.find_and_read_latest_html_file()
    parser.parse_data(html_file_contents)

    total_times = htmlparsing.get_total_times(parser)
    num_laps_driven = htmlparsing.get_num_laps_driven(parser)
    positions = htmlparsing.get_positions(total_times, num_laps_driven)
    best_laptimes = htmlparsing.get_best_laptimes(parser)
    average_laptimes = htmlparsing.get_average_laptimes(total_times, num_laps_driven)

    race_participants = htmlparsing.get_race_participants(parser)
    race, rcclass, group, start_list = _find_relevant_race(race_participants, database)

    if race is None:
        print("Couldn't match the latest result with any race!")
        print(f"Latest race had participants {race_participants}")
        return

    print(f"The latest result matches {rcclass} {group} {race}.")
    if not _confirm_yes_no():
        print("Please manually enter the result using the --manual flag")
        return

    if race not in database[RESULTS_KEY]:
        database[RESULTS_KEY][race] = {"2WD": {}, "4WD": {}}

    if group in database[RESULTS_KEY][race][rcclass]:
        print("This race already has a previous result, which will be overwritten.")
        if not _confirm_yes_no():
            return

    database[RESULTS_KEY][race][rcclass][group] = {}
    database[RESULTS_KEY][race][rcclass][group]["positions"] = positions
    database[RESULTS_KEY][race][rcclass][group]["num_laps_driven"] = num_laps_driven
    database[RESULTS_KEY][race][rcclass][group]["total_times"] = total_times
    database[RESULTS_KEY][race][rcclass][group]["best_laptimes"] = best_laptimes
    database[RESULTS_KEY][race][rcclass][group]["average_laptimes"] = average_laptimes
    database[RESULTS_KEY][race][rcclass][group]["manual"] = False

    _add_dns_participants(database[RESULTS_KEY][race][rcclass][group], start_list)

    if race == FINALS_NAME:
        _update_start_lists_for_finals(database)

    _save_database(database)

    results_text = textmessages.get_result_text_message(
        database[RESULTS_KEY][race][rcclass][group], rcclass, group, race)

    clipboard.copy(results_text)
    print(results_text)

    print("^^ Copied to clipboard")


def add_new_result_manually():
    database = _get_database()
    race = _get_current_heat(database)

    race_options = [(rcclass, group)
                    for rcclass in ("2WD", "4WD") for group in database[START_LISTS_KEY][race][rcclass]]
    rcclass, group = _select_from_list(
        race_options, "Select which race to enter manually.", lambda e: " ".join(e))

    if race not in database[RESULTS_KEY]:
        database[RESULTS_KEY][race] = {"2WD": {}, "4WD": {}}

    if group in database[RESULTS_KEY][race][rcclass]:
        print("This race already has a previous result, which will be overwritten.")
        if not _confirm_yes_no():
            return
    
    print("Enter the drivers in the order they finished.")
    positions = []
    while True:
        number = _enter_participant(positions, msg="Enter driver number (blank to end): ")
        if number is None:
            break
        positions.append(number)

    database[RESULTS_KEY][race][rcclass][group] = {}
    database[RESULTS_KEY][race][rcclass][group]["positions"] = positions
    database[RESULTS_KEY][race][rcclass][group]["num_laps_driven"] = {}
    database[RESULTS_KEY][race][rcclass][group]["total_times"] = {}
    database[RESULTS_KEY][race][rcclass][group]["best_laptimes"] = []
    database[RESULTS_KEY][race][rcclass][group]["average_laptimes"] = []
    database[RESULTS_KEY][race][rcclass][group]["manual"] = True

    _add_dns_participants(
        database[RESULTS_KEY][race][rcclass][group], database[START_LISTS_KEY][race][rcclass][group])

    if race == FINALS_NAME:
        _update_start_lists_for_finals(database)

    _save_database(database)

    results_text = textmessages.get_result_text_message(
        database[RESULTS_KEY][race][rcclass][group], rcclass, group, race)

    clipboard.copy(results_text)
    print(results_text)

    print("^^ Copied to clipboard")


def _get_latest_race_class_group(database):
    race = _get_current_heat(database)
    class_order = CLASS_ORDER[race]
    results = database[RESULTS_KEY]
    heat_results = results.get(race)
    if heat_results is None:
        previous_heat = _get_previous_heat(database)
        heat_results = database.get(previous_heat)
        if heat_results is None:
            return None, None, None

    for rcclass, group in reversed(class_order):
        class_results = heat_results[rcclass]
        if group in class_results:
            return race, rcclass, group

    return None, None, None


def show_latest_result(select=False):
    database = _get_database()
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
    

def main():
    parser = argparse.ArgumentParser(description="Manages an RCBash race day.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--new-race-day", action="store_true",
                       help="Start a new race day")
    group.add_argument("-r", "--result", action="store_true",
                       help="Add new result")
    group.add_argument("-n", "--next-round", action="store_true",
                       help="Add new result")
    group.add_argument("-d", "--show-result", action="store_true",
                       help="Display the a result as text. Use '-p'/'--select-result' flag "
                            "to select which result, if empty the latest will be shown.")

    parser.add_argument("-m", "--manual", action="store_true",
                        help="Add a result manually")
    parser.add_argument("-p", "--select-result", action="store_true",
                        help="Select a result manually")

    args = parser.parse_args()

    if args.new_race_day:
        create_qualifiers()
    elif args.result and not args.manual:
        add_new_result()
    elif args.result and args.manual:
        add_new_result_manually()
    elif args.next_round:
        start_new_race_round()
    elif args.show_result:
        show_latest_result(select=args.select_result)


if __name__ == "__main__":
    main()
