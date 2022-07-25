import flask
import racelogic.resultcalculation as rc

from racelogic.names import NAMES

from flask import Flask, request
from pathlib import Path

app = Flask(__name__)

IS_PRODUCTION = Path("/home/malcolm/isproduction").exists()

START_LISTS_TAB = "startlists"
RESULTS_TAB = "results"
POINTS_TAB = "points"

TABS = list(enumerate([
    (START_LISTS_TAB, "Startordningar", "list"),
    (RESULTS_TAB, "Resultat", "award"),
    (POINTS_TAB, "Poängställning", "bar-chart"),
]))


def _render_page(active_index, selected_date):
    db_dates = rc.get_all_dates()
    _, (active_tab, active_tab_readable, active_tab_icon) = TABS[active_index]

    start_lists = []
    if active_tab == START_LISTS_TAB:
        start_lists = rc.get_all_start_lists(selected_date)

    return flask.render_template(f"{active_tab}.html",
                                 tabs=TABS,
                                 db_dates=enumerate(db_dates),
                                 active_tab=active_tab,
                                 active_tab_readable=active_tab_readable,
                                 active_tab_icon=active_tab_icon,
                                 selected_date=selected_date,
                                 start_lists=start_lists,
                                 names=NAMES,
                                 active_index=active_index)


def _is_valid_db_date(date):
    return date in rc.get_all_dates()


# TODO remove
@app.get("/")
def index():
    return flask.redirect("/startlists")


@app.get(f"/{START_LISTS_TAB}")
def start_lists_default():
    latest = rc.get_all_dates()[0]
    return flask.redirect(f"/{START_LISTS_TAB}/{latest}")


@app.get(f"/{RESULTS_TAB}")
def results_default():
    latest = rc.get_all_dates()[0]
    return flask.redirect(f"/{RESULTS_TAB}/{latest}")


@app.get(f"/{POINTS_TAB}")
def points_default():
    latest = rc.get_all_dates()[0]
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
