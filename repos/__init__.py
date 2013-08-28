#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import

__all__ = ["app"]

import flask
import redis
from .find import find_similar

app = flask.Flask(__name__)
rdb = redis.Redis()


@app.route("/")
@app.route("/<user>/<repo>")
def index(user=None, repo=None):
    return flask.render_template("index.html")


@app.route("/api/similar")
def similar():
    reponame = flask.request.args.get("repo")
    if reponame is None:
        return (flask.jsonify(message="You must provide the 'repo' argument."),
                400)

    repos = find_similar(reponame)
    fields = ["name", "score"]
    return flask.jsonify(count=len(repos),
                         repos=[dict(zip(fields, repo)) for repo in repos])


@app.route("/api/top")
@app.route("/api/top/<int:N>")
def top(N=10):
    repolist = rdb.zrevrange("ghcf:repo:{0}".format(reponame), 0, N)
    return N
