import flask

from flask import Flask, request
from pathlib import Path

app = Flask(__name__)


@app.get("/")
@app.get("/<name>")
def index(name=None):
    return flask.render_template("index.html", name=name)


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
