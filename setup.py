#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from setuptools import setup, find_packages

install_requires = [
    "pandas>=1.2.2",
    "geopandas>=0.8.2",
    "rtree>=0.9.7",
    "scipy>=1.6.1",
    "sklearn>=0.24.1",
]

setup(
    name="Seriation map",
    packages=find_packages(),
    install_requires=install_requires
)
