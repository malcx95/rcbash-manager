from datetime import datetime
from typing import Dict, Tuple

import flask
import json

import flask_wtf.csrf

import server.racelogic.resultcalculation as rc
import server.racelogic.raceday as rd

from flask import Flask, request, Blueprint
from flask_login import login_required, logout_user, current_user, login_user
from pathlib import Path

from server import models
from server.racedayoperations import create_raceday_from_json, RaceDayException

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

NEW_RACE_DAY_TAB = "newraceday"

SEASON_POINTS_TAB = "seasonpoints"

LOGOUT_URL = "logout"

RESULT_TABLE_CLASSES = {1: "winner", 2: "second", 3: "third"}

TABS = {
    START_LISTS_TAB: ("Startordningar", "list"),
    RESULTS_TAB: ("Resultat", "award"),
    POINTS_TAB: ("Poängställning", "bar-chart"),
}

AUTHENTICATED_TABS = list(enumerate([
    (LOGOUT_URL, "Logga ut", "log-out"),
]))

ADMIN_TABS = {
    NEW_RACE_DAY_TAB: ("Ny deltävling", "plus"),
}

SEASON_TABS = {
    SEASON_POINTS_TAB: ("Cupställning", "bar-chart-2"),
}

SHORTER_FINAL_NAMES = {
    rd.EIGHTH_FINAL_NAME: "Åttondel",
    rd.QUARTER_FINAL_NAME: "Kvart",
    rd.SEMI_FINAL_NAME: "Semi",
    rd.FINALS_NAME: "Final",
}

# TODO can the admin controls just be modals on the regular pages?
# For instance, maybe you would start a new race round from the Start lists page,
# with a button only visible to admins, which opens a modal.
# The result page would just have edit buttons to edit the result or add a result manually.


def _render_page(active_tab: str, selected_date: str, selected_season: int) -> str:
    start_lists = []
    marshals = {}
    results = {}
    points = {}

    raceday = rd.get_raceday_with_date(selected_date)
    if active_tab in (START_LISTS_TAB, RESULTS_TAB):
        start_lists, marshals = rc.get_all_start_lists(raceday)
        results = raceday.get_all_results()
    elif active_tab == POINTS_TAB:
        all_points, points_per_race = rc.get_current_cup_points(selected_date)
        points = {
            rcclass: _sort_points(all_points, points_per_race, rcclass)
            for rcclass in ("2WD", "4WD")
        }

    race_order = [SHORTER_FINAL_NAMES[name] for name in rd.NON_QUALIFIER_RACE_ORDER]

    return _render_general_page(active_tab,
                                selected_date,
                                selected_season,
                                TABS,
                                start_lists=start_lists,
                                marshals=marshals,
                                results=results,
                                points=points,
                                race_order=race_order
                                )


def _render_individual_result_page(selected_date: str, result: rd.RaceResult, selected_season: int) -> str:
    active_tab = RESULTS_TAB
    laptimes_json = _create_laptimes_json(result)

    return _render_general_page(active_tab,
                                selected_date,
                                selected_season,
                                TABS,
                                template_name="resultdetails.html",
                                laptimes_json=laptimes_json,
                                results=result,
                                group=result.group,
                                heat_name=result.heat_name,
                                rcclass=result.rcclass,
                                )


def _render_season_wide_page(selected_date: str, selected_season: int, active_tab: str) -> str:

    season_points_per_class = None
    num_races = 0

    if active_tab == SEASON_POINTS_TAB:
        dates, _, locations = models.get_race_dates_filenames_and_locations(selected_season)
        racedays = [rd.get_raceday_with_date(date) for date in reversed(dates)]
        season_points_per_class = rc.calculate_season_points(racedays, list(reversed(locations)))

    return _render_general_page(active_tab,
                                selected_date,
                                selected_season,
                                SEASON_TABS,
                                template_name="totalpoints.html",
                                season_points_per_class=season_points_per_class,
                                )


def _render_admin_page(selected_date: str, selected_season: int, active_tab: str, **kwargs) -> str:
    return _render_general_page(active_tab,
                                selected_date,
                                selected_season,
                                ADMIN_TABS,
                                template_name="newraceday.html", **kwargs)


def _render_general_page(active_tab: str, selected_date: str,
                         selected_season: int, tabs: Dict[str, Tuple[str, str]],
                         template_name: str = None, **kwargs) -> str:
    is_admin, is_authenticated = check_authentication()

    all_drivers = []
    if is_admin:
        all_drivers = models.get_all_driver_numbers_and_names()

    dates, filenames, locations = models.get_race_dates_filenames_and_locations(selected_season)

    # TODO find a way to avoid having to fetch this from the database every time
    all_seasons = models.get_all_season_years()

    active_tab_readable, active_tab_icon = tabs[active_tab]

    return flask.render_template(f"{active_tab}.html" if template_name is None else template_name,
                                 active_tab=active_tab,
                                 active_tab_icon=active_tab_icon,
                                 active_tab_readable=active_tab_readable,
                                 all_drivers=all_drivers,
                                 all_seasons=all_seasons,
                                 admin_tabs=ADMIN_TABS.items(),
                                 authenticated_tabs=AUTHENTICATED_TABS,
                                 db_dates=enumerate(dates),
                                 is_admin=is_admin,
                                 is_authenticated=is_authenticated,
                                 locations=locations,
                                 result_table_classes=RESULT_TABLE_CLASSES,
                                 selected_date=selected_date,
                                 season_tabs=SEASON_TABS.items(),
                                 tabs=TABS.items(),
                                 year=selected_season,
                                 **kwargs
                                 )


def check_authentication():
    is_authenticated = current_user.is_authenticated
    is_admin = is_authenticated and models.is_user_admin(current_user)
    return is_admin, is_authenticated


def _create_laptimes_json(result):
    laptimes = {
        "average": [result.average_laptimes_dict()[driver].milliseconds / 1000.
                    for driver, _ in result.best_laptimes],
        "bestNames": [driver.name for driver, _ in result.best_laptimes],
        "bestTimes": [time.milliseconds / 1000. for _, time in result.best_laptimes]
    }
    return json.dumps(laptimes)


def _is_valid_db_date(date):
    return date in rd.get_all_dates()


def _sort_points(all_points, points_per_race, rcclass):
    # TODO this is duplicated in textmessages, this should probably be refactored
    return sorted([(num, all_points[num], _pad_list_with_nones(points_per_race[rcclass][num]))
                   for num in points_per_race[rcclass]], key=lambda k: k[1], reverse=True)


def _pad_list_with_nones(points_list):
    return points_list + [None]*(len(rd.NON_QUALIFIER_RACE_ORDER) - len(points_list))


# TODO remove
@main_bp.get("/")
def index():
    return flask.redirect("/startlists")


@main_bp.route(f"/{LOGOUT_URL}")
def logout():
    logout_user()
    return flask.redirect(flask.url_for("main_bp.index"))


@main_bp.get(f"/{START_LISTS_TAB}/<year>")
def start_lists_default_with_year(year):
    latest = models.get_latest_date(year)
    return flask.redirect(flask.url_for("main_bp.start_lists_page", year=year, date=latest))


@main_bp.get(f"/{START_LISTS_TAB}")
def start_lists_default():
    latest_season = models.get_latest_season()
    latest = models.get_latest_date(latest_season)
    return flask.redirect(flask.url_for("main_bp.start_lists_page", year=latest_season, date=latest))


@main_bp.get(f"/{RESULTS_TAB}")
def results_default():
    latest_season = models.get_latest_season()
    latest = models.get_latest_date(latest_season)
    return flask.redirect(flask.url_for("main_bp.results_page", year=latest_season, date=latest))


@main_bp.get(f"/{POINTS_TAB}")
def points_default():
    latest_season = models.get_latest_season()
    latest = models.get_latest_date(latest_season)
    return flask.redirect(flask.url_for("main_bp.points_page", year=latest_season, date=latest))


@main_bp.get(f"/{SEASON_POINTS_TAB}")
def season_points_default():
    latest_season = models.get_latest_season()
    latest = models.get_latest_date(latest_season)
    return flask.redirect(flask.url_for("main_bp.season_points_page", year=latest_season, date=latest))


@main_bp.get(f"/{NEW_RACE_DAY_TAB}")
def new_race_day_default():
    latest_season = models.get_latest_season()
    latest = models.get_latest_date(latest_season)
    return flask.redirect(flask.url_for("main_bp.new_race_day_page", year=latest_season, date=latest))


# TODO could you do the following three endpoints as a macro?
@main_bp.get(f"/{START_LISTS_TAB}/<year>/<date>")
def start_lists_page(year, date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{START_LISTS_TAB}")
    return _render_page(active_tab=START_LISTS_TAB, selected_date=date, selected_season=year)


@main_bp.get(f"/{RESULTS_TAB}/<year>/<date>")
def results_page(year, date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{RESULTS_TAB}")
    return _render_page(active_tab=RESULTS_TAB, selected_date=date, selected_season=year)


@main_bp.get(f"/{RESULTS_TAB}/<year>/<date>/race")
def results_details_page(year, date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{RESULTS_TAB}")

    heat = request.args.get("heat")
    rcclass = request.args.get("rcclass")
    group = request.args.get("group")

    raceday = rd.get_raceday_with_date(date)

    # TODO make 404 page
    if heat not in rd.RACE_ORDER:
        return flask.redirect(f"/{RESULTS_TAB}")
    if rcclass not in ("2WD", "4WD"):
        return flask.redirect(f"/{RESULTS_TAB}")
    if group not in ("A", "B", "C"):
        return flask.redirect(f"/{RESULTS_TAB}")

    result = raceday.get_result(heat, rcclass, group)
    if result is None:
        return flask.redirect(f"/{RESULTS_TAB}")

    return _render_individual_result_page(date, result, selected_season=year)


@main_bp.get(f"/{POINTS_TAB}/<year>/<date>")
def points_page(year, date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{POINTS_TAB}")
    return _render_page(active_tab=POINTS_TAB, selected_date=date, selected_season=year)


@main_bp.get(f"/{SEASON_POINTS_TAB}/<year>/<date>")
def season_points_page(year, date):
    # TODO validate year
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{SEASON_POINTS_TAB}")
    return _render_season_wide_page(selected_date=date, selected_season=year, active_tab=SEASON_POINTS_TAB)


@main_bp.get(f"/{NEW_RACE_DAY_TAB}/<year>/<date>")
def new_race_day_page(year, date):
    if not _is_valid_db_date(date):
        return flask.redirect(f"/{NEW_RACE_DAY_TAB}")
    is_admin, _ = check_authentication()
    if not is_admin:
        return flask.Response("Du måste vara administratör för att se denna sidan", 401,
                              {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return _render_admin_page(active_tab=NEW_RACE_DAY_TAB, selected_date=date,
                              selected_season=year)


@main_bp.post("/api/newraceday")
def create_new_race_day():
    is_admin, _ = check_authentication()
    if not is_admin:
        return flask.Response("Du måste vara administratör för utföra denna åtgärd", 401,
                              {'WWW-Authenticate': 'Basic realm="Login Required"'})
    data = request.get_json()
    print(data)
    try:
        year, raceday_date = create_raceday_from_json(data)
    except RaceDayException as e:
        return flask.Response(e.msg, 400, {})

    new_url = flask.url_for("main_bp.start_lists_page", year=year, date=raceday_date)
    return json.dumps({"success": True, "newUrl": new_url}), 200, {"ContentType": "application/json"}


@main_bp.get("/api/checkracedaydate")
def check_raceday_date():
    is_admin, _ = check_authentication()
    if not is_admin:
        return flask.Response("Du måste vara administratör för utföra denna åtgärd", 401,
                              {'WWW-Authenticate': 'Basic realm="Login Required"'})
    date_str = request.args.get("date")
    if date_str is None:
        return flask.Response("'date' argument is missing", 400, {})
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return flask.Response(f"'date' argument value {date_str} has an invalid format", 400, {})

    year = date.year
    return json.dumps({"seasonExists": models.does_season_exist(year),
                       "year": year,
                       "dateExists": models.raceday_exists(date)}), 200, {'ContentType': 'application/json'}
