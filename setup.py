#!/usr/bin/env python

from setuptools import setup

setup(
    name="repos",
    packages=["repos"],
    package_data={"repos": ["templates/*", "static/*"]},
    include_package_data=True,
)
