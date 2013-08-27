#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["get_random_events"]

import gzip
import json
import redis
import random
import logging
import requests
from StringIO import StringIO
from datetime import datetime, timedelta

initial_date = datetime(year=2011, day=12, month=2)
total_time = datetime.today() - initial_date
rdb = redis.Redis()


def get_random_events(tries=0):
    # Build the archive URL.
    date = initial_date + timedelta(days=random.random() ** 0.5
                                    * total_time.days)
    url = ("http://data.githubarchive.org/" + date.strftime("%Y-%m-%d")
           + "-{0}.json.gz".format(random.randint(0, 23)))

    # Download the file.
    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        if tries < 20:
            return get_random_events(tries=tries + 1)
        r.raise_for_status()

    # Parse the content.
    try:
        events = [json.loads(line.decode("utf-8", errors="ignore"))
                  for line in gzip.GzipFile(fileobj=StringIO(r.content))]
    except ValueError:
        if tries < 20:
            return get_random_events(tries=tries + 1)
        raise

    return events


def train_model(K=50, rate=0.01, alpha=0.01, beta=0.01):
    iteration = 1
    pipe = rdb.pipeline()
    while True:
        print("Iteration {0}".format(iteration))
        iteration += 1

        # Get a random event chunk.
        events = get_random_events()

        # Loop over the events.
        for event in events:
            # Parse the user involved and skip if no user was.
            actor = event.get("actor")
            if actor is None:
                continue

            # Deal with inconsistencies in the data formats.
            try:
                actor = actor.lower()
            except AttributeError:
                actor = actor.get("login")
                if actor is None:
                    continue
                actor = actor.lower()

            # Skip events that don't involve a repository.
            evttype = event.get("type")
            if evttype in (None, "GistEvent", "FollowEvent", "MemberEvent",
                           "TeamAddEvent"):
                continue

            # Determine the repository involved.
            repo = event.get("repository")
            reponame = None

            # Sometimes the repository is called "repo".
            if repo is None:
                repo = event.get("repo")
                if repo is not None:
                    reponame = repo.get("name")
            else:
                reponame = repo.get("owner") + "/" + repo.get("name")

            # Skip if no repository was involved.
            if reponame is None:
                logging.info("Event skipped because of missing repository")
                continue

            # Normalize the repository name.
            reponame = reponame.lower()

            # Get the current vectors.
            pipe.zincrby("ghcf:user:{0}".format(actor), reponame, 1)
            pipe.incr("ghcf:user:{0}:count".format(actor))
            pipe.zincrby("ghcf:repo:{0}".format(reponame), actor, 1)
            pipe.incr("ghcf:repo:{0}:count".format(reponame))
            pipe.execute()


if __name__ == "__main__":
    train_model()
