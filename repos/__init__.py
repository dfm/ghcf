#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import

__all__ = ["app"]

import flask
from .find import find_similar

app = flask.Flask(__name__)
app.debug = True


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
