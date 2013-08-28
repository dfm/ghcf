#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["get_random_events"]

import time
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


def get_random_events(rng, tries=0):
    # Build the archive URL.
    date = initial_date + timedelta(days=rng.random() ** 0.5
                                    * total_time.days)
    url = ("http://data.githubarchive.org/" + date.strftime("%Y-%m-%d")
           + "-{0}.json.gz".format(rng.randint(0, 23)))

    # Download the file.
    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        if tries < 20:
            return get_random_events(rng, tries=tries + 1)
        r.raise_for_status()

    # Parse the content.
    try:
        events = [json.loads(line.decode("utf-8", errors="ignore"))
                  for line in gzip.GzipFile(fileobj=StringIO(r.content))]
    except ValueError:
        if tries < 20:
            return get_random_events(rng, tries=tries + 1)
        raise

    return events


def train_model(rng):
    iteration = 1
    pipe = rdb.pipeline()
    while True:
        print("Iteration {0}".format(iteration))
        iteration += 1

        # Get a random event chunk.
        events = get_random_events(rng)

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

            # Sometimes there's a bug in the data and the repository doesn't
            # have an owner. Eff that shit.
            if reponame[0] == "/":
                logging.info("Event skipped because there was no repo owner.")
                continue

            # Normalize the repository name.
            reponame = reponame.lower()

            # Get the current vectors.
            pipe.zincrby("ghcf:user:{0}".format(actor), reponame, 1)
            pipe.zincrby("ghcf:count:user", actor, 1)
            pipe.zincrby("ghcf:repo:{0}".format(reponame), actor, 1)
            pipe.zincrby("ghcf:count:repo", reponame, 1)
            pipe.execute()


if __name__ == "__main__":
    from multiprocessing import Pool
    N = 10
    pool = Pool(N)
    rngs = [random.Random() for n in range(N)]
    s = time.time()
    [r.seed(s) for n, r in enumerate(rngs)]
    [r.jumpahead(n) for n, r in enumerate(rngs)]
    pool.map(train_model, rngs)
