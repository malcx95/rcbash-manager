from typing import Tuple, Dict, List

try:
    from server.racelogic.duration import Duration
    from server.racelogic.db import HeatStartLists

    from server.racelogic import db
    import server.racelogic.names
    import server.racelogic.util as util
    import server.racelogic.filelocation
except ImportError:
    # i'm sorry this is ugly
    from duration import Duration
    from db import HeatStartLists

    import htmlparsing
    import names
    import util as util
    import filelocation
    import db as db


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


def get_result_text_message(results: db.RaceResult, rcclass: str, group: str, race: str):

    def create_position_line(index, driver: db.Driver):
        name = driver.name
        medal = f"{MEDALS[index]} " if index < 3 else ""
        dns = ""
        if results.has_dns() and driver in results.dns:
            dns = "- Startade ej"
            medal = ""

        return f"{index + 1}. {driver.number} - {name} {medal}{dns}"

    def create_best_laptimes_line(index, num_time: Tuple[db.Driver, Duration]):
        driver, time = num_time
        return f"{driver.number} - {driver.name}: {time}"

    def create_average_laptimes_line(index, num_time: Tuple[db.Driver, Duration]):
        driver, time = num_time
        return f"{driver.number} - {driver.name}: {time}"

    def create_actual_times_line(index, driver: db.Driver):
        time = total_times.get(driver)
        if time is None:
            return f"{driver.number} - {driver.name}: Startade ej"
        num_laps = num_laps_driven[driver]
        return f"{driver.name} - {driver.name}: {num_laps} varv, {time}"

    total_times = results.total_times
    num_laps_driven = results.num_laps_driven
    positions = results.positions
    best_laptimes = results.best_laptimes
    average_laptimes = results.average_laptimes

    positions_text = create_ordered_list_text(
        positions, create_position_line
    )

    if not results.manual:
        best_laptimes_text = create_ordered_list_text(
            best_laptimes, create_best_laptimes_line
        )

        average_laptimes_text = create_ordered_list_text(
            average_laptimes, create_average_laptimes_line
        )

        actual_times_text = create_ordered_list_text(
            positions, create_actual_times_line
        )

        driver_with_best, _ = best_laptimes[0]

        return RESULT_TEXT_TEMPLATE.format(
            rcclass=rcclass,
            group=group,
            race=race,
            positions=positions_text,
            best_laptimes=best_laptimes_text,
            driver_with_best_time=driver_with_best.name,
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


def create_heat_start_list_text_message(
        heat_start_lists: Dict[str, HeatStartLists],
        race_order: List[Tuple[str, str]],
        heat_name: str,
        extra_text: str = "") -> str:
    start_list_texts = []
    for index, (rcclass, group) in enumerate(race_order):
        if not heat_start_lists[rcclass].has_group(group):
            continue
        start_list = heat_start_lists[rcclass].get_start_list(group)
        entries = [f"    {i + 1}. {driver.number} - {driver.name}"
                   for i, driver in enumerate(start_list)]
        previous_rcclass, previous_group = util.get_previous_group_wrap_around(
            heat_start_lists, race_order, index)
        marshal_text = f"{previous_rcclass} {previous_group}"
        # noinspection StrFormat
        start_list_texts.append(
            SINGLE_HEAT_START_LIST_TEMPLATE.format(
                rcclass=rcclass,
                group=group,
                start_list_text="\n".join(entries),
                marshals=marshal_text
            )
        )
    # noinspection StrFormat
    return HEAT_START_LIST_TEXT_TEMPLATE.format(
        race=heat_name,
        race_flag=RACE_FLAG,
        start_list_texts="\n".join(start_list_texts),
        extra_text=extra_text
    )


# noinspection StrFormat
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
            for driver, p in points:
                point_summation_list = " + ".join(str(p) for p in points_per_race[rcclass][driver])
                point_texts.append(f"{driver.number} - {driver.name}: {point_summation_list} = {p}")
        else:
            point_texts = [f"{driver.number} - {driver.name}: {p}"
                           for driver, p in points]
        list_text = "\n".join(point_texts)
        points_lists.append(f"{rcclass}:\n{list_text}")

    return POINTS_LIST_TEXT_TEMPLATE.format(
        race=race,
        points_list="\n\n".join(points_lists)
    )


# noinspection StrFormat
def create_race_start_message(heat_start_lists: Dict[str, HeatStartLists],
                              race_order: List[Tuple[str, str]],
                              race: str, rcclass: str, group: str, class_order_index: int):
    start_list = heat_start_lists[rcclass].get_start_list(group)
    previous_rcclass, previous_group = util.get_previous_group_wrap_around(
        heat_start_lists, race_order, class_order_index)
    marshal_list = heat_start_lists[previous_rcclass].get_start_list(previous_group)

    return START_MESSAGE_TEMPLATE.format(
        rcclass=rcclass,
        group=group,
        race=race,
        start_list="\n".join(f"{i + 1}. {driver.number} - {driver.name}"
                             for i, driver in enumerate(start_list)),
        marshal_rcclass=previous_rcclass,
        marshal_group=previous_group,
        marshals="\n".join(f"{i + 1}. {driver.number} - {driver.name}"
                           for i, driver in enumerate(marshal_list)),
        race_flag=RACE_FLAG
    )


def create_ordered_list_text(result, create_line):
    return "\n".join(create_line(i, item) for i, item in enumerate(result))