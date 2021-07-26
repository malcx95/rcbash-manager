from pathlib import Path
from collections import defaultdict

from names import NAMES

import json
import datetime


RESULT_FOLDER_PATH = Path.home() / "RCBashResults"


def _get_todays_filename():
    todays_date = datetime.datetime.now()
    todays_date_string = todays_date.strftime("%y%m%d")
    return todays_date_string + ".json"


def start_new_race_day():
    RESULT_FOLDER_PATH.mkdir(exist_ok=True)
    filename = _get_todays_filename()

    path = RESULT_FOLDER_PATH / filename
    
    with open(path, "w") as f:
        json.dump({}, f)

    print(f"New race day created in {str(path)}!")


def _number_already_entered(num, participants):
    for rcclass in participants:
        for start_list in participants[rcclass].values():
            if num in start_list:
                return True
    return False


def _enter_participant(participants):
    while True:
        number = input("Enter a participant (blank to end group): ")
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


def _confirm_group_done(start_list, rcclass, group):
    print(f"This is the start list for {rcclass} {group}:")
    print("\n".join(f"{i+1}. {num} - {NAMES[num]}" for i, num in enumerate(start_list)))

    while True:
        ans = input("Confirm? (y/n): ")
        if ans in ("y", "n"):
            return ans == "y"


def _remove_empty_groups(participants):
    new_participants = {}
    for rcclass, groups in participants.items():
        new_participants[rcclass] = {}
        for group, start_list in groups.items():
            if start_list:
                new_participants[rcclass][group] = start_list
    return new_participants


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
    return _remove_empty_groups(participants)


if __name__ == "__main__":
    add_participants()
