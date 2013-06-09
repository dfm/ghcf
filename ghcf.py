#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["get_random_events"]

import gzip
import json
import redis
import random
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


def parse_vector(v, K):
    vector = None
    if v is not None:
        try:
            vector = map(float, v.split(","))
        except Exception as e:
            print(e)
        else:
            if len(vector) != K:
                print("Dimension mismatch")
                vector = None

    if vector is None:
        vector = [0.3 * random.random() for i in range(K)]

    return vector


def update_vectors(v1, v2, rate, alpha, beta):
    zipped = zip(v1, v2)
    value = sum([a * b for a, b in zipped])
    err = 1 - value
    return ([u + rate * (err * o * u - alpha * u) for u, o in zipped],
            [u + rate * (err * o * u - beta * u) for o, u in zipped])


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

            # What type of event was this?
            evttype = event.get("type")
            if evttype == "GistEvent":
                continue

            # Get the payload.
            payload = event.get("payload", {})

            # Deal with user-user interactions.
            other = None
            if evttype == "FollowEvent":
                other = payload.get("target")
            elif evttype == "MemberEvent":
                other = payload.get("member")
            elif evttype == "TeamAddEvent":
                other = payload.get("user")

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

            # Take note of the interaction between this user and the owner of
            # the repository.
            if other is None and reponame is not None:
                other = reponame.split("/")[0]

            if other is not None:
                # Deal with inconsistencies in the data formats.
                try:
                    other = other.lower()
                except AttributeError:
                    other = other.get("login")
                    if other is not None:
                        other = other.lower()

            # Make sure that we can update.
            if reponame is None and (other is None or other == actor):
                continue

            # Get the current vectors.
            pipe.get("ghcf:user:{0}".format(actor))
            if other is not None and other != actor:
                pipe.get("ghcf:user:{0}".format(other))
            if reponame is not None:
                pipe.get("ghcf:repo:{0}".format(reponame))
            vectors = pipe.execute()

            # Parse the vectors.
            user_vector = parse_vector(vectors[0], K)
            other_vector, repo_vector = None, None
            if other is not None and other != actor:
                other_vector = parse_vector(vectors[1], K)
            if reponame is not None:
                repo_vector = parse_vector(vectors[-1], K)

            # Update the vectors.
            if other_vector is not None:
                user_vector, other_vector = update_vectors(user_vector,
                                                           other_vector,
                                                           rate, alpha, alpha)
            if repo_vector is not None:
                user_vector, repo_vector = update_vectors(user_vector,
                                                          repo_vector,
                                                          rate, alpha, beta)

            # Save to the database.
            pipe.set("ghcf:user:{0}".format(actor),
                     ",".join(map(unicode, user_vector)))
            if other_vector is not None:
                pipe.set("ghcf:user:{0}".format(other),
                         ",".join(map(unicode, other_vector)))
            if repo_vector is not None:
                pipe.set("ghcf:repo:{0}".format(reponame),
                         ",".join(map(unicode, repo_vector)))
            pipe.execute()


if __name__ == "__main__":
    train_model()
