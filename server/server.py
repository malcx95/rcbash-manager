import flask
import json

import server.racelogic.resultcalculation as rc
import server.racelogic.db as db

from flask import Flask, request, Blueprint
from flask_login import login_required, logout_user, current_user, login_user
from pathlib import Path


main_bp = Blueprint(
    "main_bp",
    __name__,
    template_folder="templates",
    static_folder="static"
)

IS_PRODUCTION = Path("/home/malcolm/isproduction").exists()

START_LISTS_TAB = "startlists"
RESULTS_TAB = "results"
POINTS_TAB = "points"

LOGOUT_URL = "logout"

RESULT_TABLE_CLASSES = {1: "winner", 2: "second", 3: "third"}

TABS = list(enumerate([
    (START_LISTS_TAB, "Startordningar", "list"),
    (RESULTS_TAB, "Resultat", "award"),
    (POINTS_TAB, "Poängställning", "bar-chart"),
]))

AUTHENTICATED_TABS = list(enumerate([
    (LOGOUT_URL, "Logga ut", "log-out"),
]))


SHORTER_FINAL_NAMES = {
    db.EIGHTH_FINAL_NAME: "Åttondel",
    db.QUARTER_FINAL_NAME: "Kvart",
    db.SEMI_FINAL_NAME: "Semi",
    db.FINALS_NAME: "Final",
}


def _render_page(active_index: int, selected_date: str) -> str:
    is_authenticated = current_user.is_authenticated
    db_dates = db.get_all_dates()
    _, (active_tab, active_tab_readable, active_tab_icon) = TABS[active_index]

    start_lists = []
    marshals = {}
    results = {}
    points = {}

    database = db.get_database_with_date(selected_date)
    if active_tab in (START_LISTS_TAB, RESULTS_TAB):
        start_lists, marshals = rc.get_all_start_lists(database)
        results = database.get_all_results()
    elif active_tab == POINTS_TAB:
        all_points, points_per_race = rc.get_current_cup_points(selected_date)
        points = {
            rcclass: _sort_points(all_points, points_per_race, rcclass)
            for rcclass in ("2WD", "4WD")
        }

    race_order = [SHORTER_FINAL_NAMES[name] for name in db.NON_QUALIFIER_RACE_ORDER]

    return flask.render_template(f"{active_tab}.html",
                                 tabs=TABS,
                                 authenticated_tabs=AUTHENTICATED_TABS,
                                 db_dates=enumerate(db_dates),
                                 active_tab=active_tab,
                                 active_tab_readable=active_tab_readable,
                                 active_tab_icon=active_tab_icon,
                                 selected_date=selected_date,
                                 start_lists=start_lists,
                                 marshals=marshals,
                                 results=results,
                                 result_table_classes=RESULT_TABLE_CLASSES,
                                 points=points,
                                 race_order=race_order,
                                 active_index=active_index,
                                 is_authenticated=is_authenticated,
                                 )


def _render_individual_result_page(selected_date: str, result: db.RaceResult) -> str:
    active_index = 1
    db_dates = db.get_all_dates()
    _, (active_tab, active_tab_readable, active_tab_icon) = TABS[active_index]

    laptimes_json = _create_laptimes_json(result)

    return flask.render_template("resultdetails.html",
                                 tabs=TABS,
                                 db_dates=enumerate(db_dates),
                                 active_tab=active_tab,
                                 active_tab_readable=active_tab_readable,
                                 active_tab_icon=active_tab_icon,
                                 selected_date=selected_date,
                                 heat_name=result.heat_name,
                                 rcclass=result.rcclass,
                                 group=result.group,
                                 results=result,
                                 laptimes_json=laptimes_json,
                                 result_table_classes=RESULT_TABLE_CLASSES,
                                 active_index=active_index)


def _create_laptimes_json(result):
    laptimes = {
        "average": [result.average_laptimes_dict()[driver].milliseconds / 1000.
                    for driver, _ in result.best_laptimes],
        "bestNames": [driver.name for driver, _ in result.best_laptimes],
        "bestTimes": [time.milliseconds / 1000. for _, time in result.best_laptimes]
    }
    return json.dumps(laptimes)


def _is_valid_db_date(date):
    return date in db.get_all_dates()


def _sort_points(all_points, points_per_race, rcclass):
    # TODO this is duplicated in textmessages, this should probably be refactored
    return sorted([(num, all_points[num], _pad_list_with_nones(points_per_race[rcclass][num]))
                   for num in points_per_race[rcclass]], key=lambda k: k[1], reverse=True)


def _pad_list_with_nones(points_list):
    return points_list + [None]*(len(db.NON_QUALIFIER_RACE_ORDER) - len(points_list))


# TODO remove
@main_bp.get("/")
def index():
    return flask.redirect("/startlists")


@main_bp.route(f"/{LOGOUT_URL}")
def logout():
    logout_user()
    return flask.redirect(flask.url_for("main_bp.index"))


@main_bp.get(f"/{START_LISTS_TAB}")
def start_lists_default():
    latest = db.get_all_dates()[0]
    return flask.redirect(f"/{START_LISTS_TAB}/{latest}")


@main_bp.get(f"/{RESULTS_TAB}")
def results_default():
    latest = db.get_all_dates()[0]
    return flask.redirect(f"/{RESULTS_TAB}/{latest}")


@main_bp.get(f"/{POINTS_TAB}")
def points_default():
    latest = db.get_all_dates()[0]
    return flask.redirect(f"/{POINTS_TAB}/{latest}")


# TODO could you do the following three endpoints as a macro?
@main_bp.get(f"/{START_LISTS_TAB}/<date>")
def start_lists_page(date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{START_LISTS_TAB}")
    return _render_page(active_index=0, selected_date=date)


@main_bp.get(f"/{RESULTS_TAB}/<date>")
def results_page(date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{RESULTS_TAB}")
    return _render_page(active_index=1, selected_date=date)


@main_bp.get(f"/{RESULTS_TAB}/<date>/race")
def results_details_page(date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{RESULTS_TAB}")

    heat = request.args.get("heat")
    rcclass = request.args.get("rcclass")
    group = request.args.get("group")

    database = db.get_database_with_date(date)

    # TODO make 404 page
    if heat not in db.RACE_ORDER:
        return flask.redirect(f"/{RESULTS_TAB}")
    if rcclass not in ("2WD", "4WD"):
        return flask.redirect(f"/{RESULTS_TAB}")
    if group not in ("A", "B", "C"):
        return flask.redirect(f"/{RESULTS_TAB}")

    result = database.get_result(heat, rcclass, group)
    if result is None:
        return flask.redirect(f"/{RESULTS_TAB}")

    return _render_individual_result_page(date, result)


@main_bp.get(f"/{POINTS_TAB}/<date>")
def points_page(date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{POINTS_TAB}")
    return _render_page(active_index=2, selected_date=date)


@main_bp.get("/<path:path>")
def get_static(path):
    return flask.send_from_directory("static", path)

