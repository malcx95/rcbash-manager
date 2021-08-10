from duration import Duration
from functools import reduce

import htmlparsing
import names

#import matplotlib.pyplot as plt
import filelocation
import numpy as np
import argparse
import sys


CLASSES = {2: "2WD", 4: "4WD"}
RACES = {
    16: "Kval",
    8: "Åttondelsfinal",
    4: "Fjärdedelsfinal",
    2: "Semifinal",
    1: "Final",
}

GOLD_MEDAL = "🥇"
SILVER_MEDAL = "🥈"
BRONZE_MEDAL = "🥉"

MEDALS = [GOLD_MEDAL, SILVER_MEDAL, BRONZE_MEDAL]

RESULT_TEXT_TEMPLATE = \
"""Resultat från {rcclass} {group} {race}

{positions}

Bästa varvtider:
{best_laptimes}
varav allra bästa gjordes av {driver_with_best_time}!

Genomsnittliga varvtider:
{average_laptimes}

Totala tider:
{actual_times}
"""

RESULT_TEXT_TEMPLATE_MANUAL = \
"""Resultat från {rcclass} {group} {race}

{positions}
"""


def get_result_text_message(results, rcclass, group, race):

    def create_position_line(index, number):
        driver = names.NAMES[number]
        time = total_times.get(number)
        medal = f"{MEDALS[index]} " if index < 3 else ""
        return f"{index + 1}. {number} - {driver} {medal}"

    def create_best_laptimes_line(index, num_time):
        number, time = num_time
        driver = names.NAMES[number]
        return f"{number} - {driver}: {time}"

    def create_average_laptimes_line(index, num_time):
        number, time = num_time
        driver = names.NAMES[number]
        return f"{number} - {driver}: {time}"

    def create_actual_times_line(index, number):
        driver = names.NAMES[number]
        time = total_times.get(number)
        if time is None:
            return f"{number} - {driver}: Startade ej"
        num_laps = num_laps_driven[number]
        return f"{number} - {driver}: {num_laps} varv, {time}"

    total_times = results["total_times"]
    num_laps_driven = results["num_laps_driven"]
    positions = results["positions"]
    best_laptimes = results["best_laptimes"]
    average_laptimes = results["average_laptimes"]

    positions_text = create_ordered_list_text(
        positions, create_position_line
    )

    if not results["manual"]:
        best_laptimes_text = create_ordered_list_text(
            best_laptimes, create_best_laptimes_line
        )

        average_laptimes_text = create_ordered_list_text(
            average_laptimes, create_average_laptimes_line
        )

        actual_times_text = create_ordered_list_text(
            positions, create_actual_times_line
        )

        num_with_best, _ = best_laptimes[0]
        driver_with_best = names.NAMES[num_with_best]

        return RESULT_TEXT_TEMPLATE.format(
            rcclass=rcclass,
            group=group,
            race=race,
            positions=positions_text,
            best_laptimes=best_laptimes_text,
            driver_with_best_time=driver_with_best,
            average_laptimes=average_laptimes_text,
            actual_times=actual_times_text
        )
    else:
        return RESULT_TEXT_TEMPLATE_MANUAL.format(
            rcclass=rcclass,
            group=group,
            race=race,
            positions=positions_text
        )


def create_ordered_list_text(result, create_line):
    return "\n".join(create_line(i, item) for i, item in enumerate(result))


def main():
    argparser = argparse.ArgumentParser(description="Time to race!")
    argparser.add_argument("-c", "--rcclass", type=int, required=True, help="2 for 2WD, 4 for 4WD")
    argparser.add_argument("-g", "--group", type=str, required=True,
                           help="A, B or C")
    argparser.add_argument("-r", "--race", type=int, required=True,
                           help="16, 8, 4, 2 or 1")

    args = argparser.parse_args()
    if args.rcclass not in CLASSES:
        parser.error("Class must be 2 or 4")
        sys.exit(-1)

    if args.race not in RACES:
        parser.error("Class must be 1, 2, 4, 8 or 16")
        sys.exit(-1)

    parser = htmlparsing.RCMHtmlParser()

    html_file_contents = filelocation.find_and_read_latest_html_file()

    parser.parse_data(html_file_contents)

    total_times = htmlparsing.get_total_times(parser)
    num_laps_driven = htmlparsing.get_num_laps_driven(parser)
    positions = htmlparsing.get_positions(total_times, num_laps_driven)
    best_laptimes = htmlparsing.get_best_laptimes(parser)
    average_laptimes = htmlparsing.get_average_laptimes(total_times, num_laps_driven)

    text = get_text_message(total_times, num_laps_driven, positions,
                            best_laptimes, average_laptimes,
                            CLASSES[args.rcclass], args.group, RACES[args.race])

    clipboard.copy(text)
    print(text)


if __name__ == "__main__":
    main()
