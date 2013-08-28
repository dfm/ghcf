#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["find_similar"]

import redis
from math import log10, sqrt
from collections import defaultdict

rdb = redis.Redis()


def find_similar(reponame, N=10):
    # Normalize the repository name.
    reponame = reponame.lower()

    # Check the cache.
    values = rdb.zrevrange("ghcf:cache:{0}".format(reponame), 0, N-1,
                           withscores=True)
    if len(values):
        return values

    # Find the users that have interacted with the requested repository.
    userlist = rdb.zrevrange("ghcf:repo:{0}".format(reponame), 0, -1)

    # Loop over the users and find which repositories the user has interacted
    # with.
    pipe = rdb.pipeline()
    [pipe.zrevrange("ghcf:user:{0}".format(user), 0, -1) for user in userlist]

    # Count the number of interactions with each repository.
    repos = [v for repos in pipe.execute() for v in repos]
    repodict = defaultdict(int)
    for repo in repos:
        repodict[repo] += 1

    # Remove the initial repository.
    repodict.pop(reponame, None)

    # Return if there are no results.
    if not len(repodict):
        return []

    # Split the names and similarities to ensure ordering.
    names, similarities = zip(*repodict.items())

    # Get the "popularity" of the similar repositories.
    [pipe.zscore("ghcf:count:repo", r) for r in names]
    scores = [int(v) if v is not None else 1 for v in pipe.execute()]

    # Compute the final scores.
    final = zip(names, map(sum, zip(similarities,
                                    map(sqrt, map(log10, scores)))))

    # Update the cache.
    pipe.zadd("ghcf:cache:{0}".format(reponame),
              *[v for row in final for v in row])
    pipe.expire("ghcf:cache:{0}".format(reponame), 3600)
    pipe.execute()

    return sorted(final, key=lambda v: v[1], reverse=True)[:N]


if __name__ == "__main__":
    print(find_similar("numpy/numpy"))
