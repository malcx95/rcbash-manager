from duration import Duration
from functools import reduce
from htmlparsing import RCMHtmlParser

#import matplotlib.pyplot as plt
import filelocation
import numpy as np
import clipboard
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

TEXT_TEMPLATE = \
"""Resultat från {rcclass} {group} {race}

{positions}

Bästa varvtider:
{best_laptimes}
varav allra bästa gjordes av {driver_with_best_time}!

Genomsnittliga varvtider:
{average_laptimes}

Faktiska tider:
{actual_times}
"""


def get_total_times(parser):
    return {(number, driver): reduce(lambda a, b: a + b, laptimes, Duration(0))
            for (number, driver), laptimes in parser.result.items()}


def get_num_laps_driven(parser):
    return {(number, driver): max(0, len(laptimes) - 1)
            for (number, driver), laptimes in parser.result.items()}


def get_positions(total_times, num_laps_driven):
    orderings = []
    for (number, driver), num_laps_driven in num_laps_driven.items():
        orderings.append(((number, driver), num_laps_driven, total_times[(number, driver)]))

    orderings_sorted = sorted(orderings, key=lambda k: (k[1], -k[2].milliseconds), reverse=True)

    return [(number, driver) for (number, driver), _, _ in orderings_sorted]


def get_best_laptimes(parser):
    best_times = [(number, driver, min(laptimes[1:], key=lambda lt: lt.milliseconds))
                  if len(laptimes) > 1 else None for (number, driver),
                  laptimes in parser.result.items()]
    return sorted(best_times, key=lambda k: k[2])


def get_average_laptimes(total_times, num_laps_driven):
    average_laptimes = []
    for (number, driver), total_time in total_times.items():
        laps_driven = num_laps_driven[(number, driver)]
        if laps_driven > 0:
            average_laptimes.append((number, driver, Duration(total_time.milliseconds // laps_driven)))

    return average_laptimes


def get_text_message(total_times, num_laps_driven, positions,
                     best_laptimes, average_laptimes,
                     rcclass, group, race):

    def create_position_line(index, position):
        number, driver = position
        time = total_times[(number, driver)]
        medal = f"{MEDALS[index]} " if index < 3 else ""
        return f"{index + 1}. {number} - {driver} {medal}"

    def create_best_laptimes_line(index, num_driver_time):
        number, driver, time = num_driver_time
        return f"{number} - {driver}: {time}"

    def create_average_laptimes_line(index, num_driver_time):
        number, driver, time = num_driver_time
        return f"{number} - {driver}: {time}"

    def create_actual_times_line(index, position):
        number, driver = position
        time = total_times[(number, driver)]
        num_laps = num_laps_driven[(number, driver)]
        return f"{number} - {driver}: {num_laps} varv, {time}"

    positions_text = create_ordered_list_text(
        positions, create_position_line
    )

    best_laptimes_text = create_ordered_list_text(
        best_laptimes, create_best_laptimes_line
    )

    average_laptimes_text = create_ordered_list_text(
        average_laptimes, create_average_laptimes_line
    )

    actual_times_text = create_ordered_list_text(
        positions, create_actual_times_line
    )

    _, driver_with_best, _ = best_laptimes[0]

    return TEXT_TEMPLATE.format(
        rcclass=rcclass,
        group=group,
        race=race,
        positions=positions_text,
        best_laptimes=best_laptimes_text,
        driver_with_best_time=driver_with_best,
        average_laptimes=average_laptimes_text,
        actual_times=actual_times_text
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

    parser = RCMHtmlParser()

    html_file_contents = filelocation.find_and_read_latest_html_file()

    parser.parse_data(html_file_contents)

    total_times = get_total_times(parser)
    num_laps_driven = get_num_laps_driven(parser)
    positions = get_positions(total_times, num_laps_driven)
    best_laptimes = get_best_laptimes(parser)
    average_laptimes = get_average_laptimes(total_times, num_laps_driven)

    text = get_text_message(total_times, num_laps_driven, positions,
                            best_laptimes, average_laptimes,
                            CLASSES[args.rcclass], args.group, RACES[args.race])

    clipboard.copy(text)
    print(text)


if __name__ == "__main__":
    main()
