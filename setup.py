#!/usr/bin/env python

from setuptools import setup

setup(
    name="repos",
    packages=["repos"],
    # package_data={"": ["templates/*", "static/css/*.css",
    #                    "static/img/*", "static/js/*.js"]},
    include_package_data=True,
)