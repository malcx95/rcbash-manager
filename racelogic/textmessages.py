from racelogic.duration import Duration
from functools import reduce

import racelogic.htmlparsing
import racelogic.names

import racelogic.filelocation
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

RACE_FLAG = "🏁"

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
{actual_times}"""

HEAT_START_LIST_TEXT_TEMPLATE = \
"""Startordningar för {race}-heaten! {race_flag}

{start_list_texts}
{extra_text}"""

SINGLE_HEAT_START_LIST_TEMPLATE = \
"""{rcclass} {group}:
{start_list_text}
    {marshals} vänder bilar.
"""

RESULT_TEXT_TEMPLATE_MANUAL = \
"""Resultat från {rcclass} {group} {race}

{positions}"""

POINTS_LIST_TEXT_TEMPLATE = \
"""Nuvarande poängställning efter {race}-heaten!

{points_list}"""


START_MESSAGE_TEMPLATE = \
"""Nu ska {rcclass} {group}-{race} köras:

{start_list}

{marshal_rcclass} {marshal_group} vänder bilar, dvs:

{marshals}

Gör er redo och lycka till! {race_flag}"""


def get_result_text_message(results, rcclass, group, race):

    def create_position_line(index, number):
        driver = names.NAMES[number]
        time = total_times.get(number)
        medal = f"{MEDALS[index]} " if index < 3 else ""
        dns = ""
        if "dns" in results and number in results["dns"]:
            dns = "- Startade ej"
            medal = ""

        return f"{index + 1}. {number} - {driver} {medal}{dns}"

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


def _get_previous_group_wrap_around(heat_start_lists, race_order, index):
    # FIXME this code does not belong in this file
    temp_index = index
    while True:
        if temp_index == 0:
            temp_index = len(race_order) - 1
        else:
            temp_index -= 1
        previous_rcclass, previous_group = race_order[temp_index]

        if previous_group in heat_start_lists[previous_rcclass]:
            return previous_rcclass, previous_group


def create_heat_start_list_text_message(heat_start_lists, race_order, race, extra_text=""):
    start_list_texts = []
    for index, (rcclass, group) in enumerate(race_order):
        # FIXME this code does not belong in this file
        if group not in heat_start_lists[rcclass]:
            continue
        start_list = heat_start_lists[rcclass][group]
        entries = [f"    {i + 1}. {number} - {names.NAMES[number]}"
                   for i, number in enumerate(start_list)]
        previous_rcclass, previous_group = _get_previous_group_wrap_around(
            heat_start_lists, race_order, index)
        marshal_text = f"{previous_rcclass} {previous_group}"
        start_list_texts.append(
            SINGLE_HEAT_START_LIST_TEMPLATE.format(
                rcclass=rcclass,
                group=group,
                start_list_text="\n".join(entries),
                marshals=marshal_text
            )
        )
    return HEAT_START_LIST_TEXT_TEMPLATE.format(
        race=race,
        race_flag=RACE_FLAG,
        start_list_texts="\n".join(start_list_texts),
        extra_text=extra_text
    )


def create_points_list_text_message(all_points, points_per_race, race, verbose):
    points_lists = []
    for rcclass in points_per_race:
        points = sorted(
            [(num, all_points[num]) for num in points_per_race[rcclass]],
            key=lambda k: k[1],
            reverse=True
        )
        if verbose:
            point_texts = []
            for num, p in points:
                point_summation_list = " + ".join(str(p) for p in points_per_race[rcclass][num])
                point_texts.append(f"{num} - {names.NAMES[num]}: {point_summation_list} = {p}")
        else:
            point_texts = [f"{num} - {names.NAMES[num]}: {p}"
                           for num, p in points]
        list_text = "\n".join(point_texts)
        points_lists.append(f"{rcclass}:\n{list_text}")

    return POINTS_LIST_TEXT_TEMPLATE.format(
        race=race,
        points_list="\n\n".join(points_lists)
    )


def create_race_start_message(heat_start_lists, race_order, race, rcclass, group, class_order_index):
    start_list = heat_start_lists[rcclass][group]
    previous_rcclass, previous_group = _get_previous_group_wrap_around(
        heat_start_lists, race_order, class_order_index)
    marshal_list = heat_start_lists[previous_rcclass][previous_group]

    return START_MESSAGE_TEMPLATE.format(
        rcclass=rcclass,
        group=group,
        race=race,
        start_list="\n".join(f"{i + 1}. {num} - {names.NAMES[num]}" for i, num in enumerate(start_list)),
        marshal_rcclass=previous_rcclass,
        marshal_group=previous_group,
        marshals="\n".join(f"{i + 1}. {num} - {names.NAMES[num]}" for i, num in enumerate(marshal_list)),
        race_flag=RACE_FLAG
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
