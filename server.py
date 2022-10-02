import flask
import json

import racelogic.db
import racelogic.resultcalculation as rc
import racelogic.db as db
from racelogic.names import NAMES

from flask import Flask, request
from pathlib import Path

app = Flask(__name__)

IS_PRODUCTION = Path("/home/malcolm/isproduction").exists()

START_LISTS_TAB = "startlists"
RESULTS_TAB = "results"
POINTS_TAB = "points"

RESULT_TABLE_CLASSES = {1: "winner", 2: "second", 3: "third"}

TABS = list(enumerate([
    (START_LISTS_TAB, "Startordningar", "list"),
    (RESULTS_TAB, "Resultat", "award"),
    (POINTS_TAB, "Poängställning", "bar-chart"),
]))


SHORTER_FINAL_NAMES = {
    db.EIGHTH_FINAL_NAME: "Åttondel",
    db.QUARTER_FINAL_NAME: "Kvart",
    db.SEMI_FINAL_NAME: "Semi",
    db.FINALS_NAME: "Final",
}


def _render_page(active_index, selected_date):
    db_dates = db.get_all_dates()
    _, (active_tab, active_tab_readable, active_tab_icon) = TABS[active_index]

    start_lists = []
    marshals = {}
    results = {}
    points = {}
    if active_tab in (START_LISTS_TAB, RESULTS_TAB):
        start_lists, marshals = rc.get_all_start_lists(selected_date)
        results = rc.get_all_results(selected_date)
    elif active_tab == POINTS_TAB:
        all_points, points_per_race = rc.get_current_cup_points(selected_date)
        points = {
            rcclass: _sort_points(all_points, points_per_race, rcclass)
            for rcclass in ("2WD", "4WD")
        }

    race_order = [SHORTER_FINAL_NAMES[name] for name in racelogic.db.NON_QUALIFIER_RACE_ORDER]

    return flask.render_template(f"{active_tab}.html",
                                 tabs=TABS,
                                 db_dates=enumerate(db_dates),
                                 active_tab=active_tab,
                                 active_tab_readable=active_tab_readable,
                                 active_tab_icon=active_tab_icon,
                                 selected_date=selected_date,
                                 start_lists=start_lists,
                                 marshals=marshals,
                                 names=NAMES,
                                 results=results,
                                 result_table_classes=RESULT_TABLE_CLASSES,
                                 points=points,
                                 race_order=race_order,
                                 active_index=active_index)


def _render_individual_result_page(selected_date, results):
    active_index = 1
    db_dates = db.get_all_dates()
    _, (active_tab, active_tab_readable, active_tab_icon) = TABS[active_index]

    laptimes_json = _create_laptimes_json(results)

    return flask.render_template("resultdetails.html",
                                 tabs=TABS,
                                 db_dates=enumerate(db_dates),
                                 active_tab=active_tab,
                                 active_tab_readable=active_tab_readable,
                                 active_tab_icon=active_tab_icon,
                                 selected_date=selected_date,
                                 names=NAMES,
                                 heat_name=results.heat_name,
                                 rcclass=results.rcclass,
                                 group=results.group,
                                 results=results,
                                 laptimes_json=laptimes_json,
                                 result_table_classes=RESULT_TABLE_CLASSES,
                                 active_index=active_index)


def _create_laptimes_json(results):
    laptimes = {
        "average": [results.average_laptimes_dict()[num].milliseconds / 1000.
                    for num, _ in results.best_laptimes],
        "bestNames": [NAMES[num] for num, _ in results.best_laptimes],
        "bestTimes": [time.milliseconds / 1000. for _, time in results.best_laptimes]
    }
    return json.dumps(laptimes)


def _is_valid_db_date(date):
    return date in db.get_all_dates()


def _sort_points(all_points, points_per_race, rcclass):
    # TODO this is duplicated in textmessages, this should probably be refactored
    return sorted([(num, all_points[num], _pad_list_with_nones(points_per_race[rcclass][num]))
                   for num in points_per_race[rcclass]], key=lambda k: k[1], reverse=True)

def _pad_list_with_nones(points_list):
    return points_list + [None]*(len(racelogic.db.NON_QUALIFIER_RACE_ORDER) - len(points_list))


# TODO remove
@app.get("/")
def index():
    return flask.redirect("/startlists")


@app.get(f"/{START_LISTS_TAB}")
def start_lists_default():
    latest = db.get_all_dates()[0]
    return flask.redirect(f"/{START_LISTS_TAB}/{latest}")


@app.get(f"/{RESULTS_TAB}")
def results_default():
    latest = db.get_all_dates()[0]
    return flask.redirect(f"/{RESULTS_TAB}/{latest}")


@app.get(f"/{POINTS_TAB}")
def points_default():
    latest = db.get_all_dates()[0]
    return flask.redirect(f"/{POINTS_TAB}/{latest}")


# TODO could you do the following three endpoints as a macro?
@app.get(f"/{START_LISTS_TAB}/<date>")
def start_lists(date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{START_LISTS_TAB}")
    return _render_page(active_index=0, selected_date=date)


@app.get(f"/{RESULTS_TAB}/<date>")
def results(date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{RESULTS_TAB}")
    return _render_page(active_index=1, selected_date=date)


@app.get(f"/{RESULTS_TAB}/<date>/race")
def results_details(date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{RESULTS_TAB}")

    heat = request.args.get("heat")
    rcclass = request.args.get("rcclass")
    group = request.args.get("group")

    # TODO make 404 page
    if heat not in racelogic.db.RACE_ORDER:
        return flask.redirect(f"/{RESULTS_TAB}")
    if rcclass not in ("2WD", "4WD"):
        return flask.redirect(f"/{RESULTS_TAB}")
    if group not in ("A", "B", "C"):
        return flask.redirect(f"/{RESULTS_TAB}")

    results = rc.get_result(date, heat, rcclass, group)
    if results is None:
        return flask.redirect(f"/{RESULTS_TAB}")

    return _render_individual_result_page(date, results)


@app.get(f"/{POINTS_TAB}/<date>")
def points(date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{POINTS_TAB}")
    return _render_page(active_index=2, selected_date=date)


@app.get("/<path:path>")
def get_static(path):
    return flask.send_from_directory("static", path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=not IS_PRODUCTION)
