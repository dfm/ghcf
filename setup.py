#!/usr/bin/env python

from setuptools import setup

setup(
    name="repos",
    packages=["repos"],
    package_data={"": ["templates/*", ]},
    include_package_data=True,
)
