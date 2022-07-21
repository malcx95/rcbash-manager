import flask
import racelogic.resultcalculation as rc

from flask import Flask, request
from pathlib import Path

app = Flask(__name__)

TABS = list(enumerate([
    ("startlists", "Startordningar", "list"),
    ("results", "Resultat", "award"),
    ("points", "Poängställning", "bar-chart"),
]))


def _render_page(active_index, selected_date):
    db_dates = rc.get_all_database_names()
    _, (active_tab, active_tab_readable, active_tab_icon) = TABS[active_index]
    return flask.render_template(f"{active_tab}.html",
                                 tabs=TABS,
                                 db_dates=enumerate(db_dates),
                                 active_tab=active_tab,
                                 active_tab_readable=active_tab_readable,
                                 active_tab_icon=active_tab_icon,
                                 selected_date=selected_date,
                                 active_index=active_index)


def _is_valid_db_date(date):
    return date in rc.get_all_database_names()


# TODO remove
@app.get("/")
def index():
    return flask.redirect("/startlists")


@app.get("/startlists")
def start_lists_default():
    latest = rc.get_all_database_names()[0]
    return flask.redirect(f"/startlists/{latest}")


@app.get("/results")
def results_default():
    latest = rc.get_all_database_names()[0]
    return flask.redirect(f"/results/{latest}")


@app.get("/points")
def points_default():
    latest = rc.get_all_database_names()[0]
    return flask.redirect(f"/points/{latest}")


# TODO could you do the following three endpoints as a macro?
@app.get("/startlists/<date>")
def start_lists(date):
    if not _is_valid_db_date(date):
        return flask.redirect("/startlists")
    return _render_page(active_index=0, selected_date=date)


@app.get("/results/<date>")
def results(date):
    if not _is_valid_db_date(date):
        return flask.redirect("/results")
    return _render_page(active_index=1, selected_date=date)


@app.get("/points/<date>")
def points(date):
    if not _is_valid_db_date(date):
        return flask.redirect("/points")
    return _render_page(active_index=2, selected_date=date)


@app.get("/<path:path>")
def get_static(path):
    return flask.send_from_directory("static", path)


@app.get("/api/test")
def test_endpoint():
    hejsan = request.args.get("hejsan")
    if hejsan is None:
        return "tjo bre"
    else:
        return f"{hejsan} heter du"
