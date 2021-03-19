#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

install_requires = [
    "pandas>=1.2.2",
    "geopandas>=0.9.0",
    "rtree>=0.9.7",
    "scipy>=1.6.1",
    "sklearn>=0.24.1",
    "dash>=1.19.0",
    "dash-bootstrap-components>=0.11.3",
]

setup(
    name="Seriation map",
    packages=find_packages(),
    install_requires=install_requires
)
