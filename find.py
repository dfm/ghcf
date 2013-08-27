#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

import redis
from collections import defaultdict

rdb = redis.Redis()


def find_similar(reponame):
    pipe = rdb.pipeline()
    pipe.zrevrange("ghcf:repo:{0}".format(reponame), 0, -1)
    userlist = pipe.execute()[0]
    repo_dict = defaultdict(int)
    for user in userlist:
        pipe.zrevrange("ghcf:user:{0}".format(user), 0, -1)
        repos = pipe.execute()[0]
        for repo in repos:
            repo_dict[repo] += 1
    print(sorted(repo_dict, key=lambda k: repo_dict[k], reverse=True)[:10])


if __name__ == "__main__":
    find_similar("dfm/ugly")
