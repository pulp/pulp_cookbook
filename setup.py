#!/usr/bin/env python3

import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


with open("requirements.txt") as requirements:
    requirements = requirements.readlines()

with open("README.rst") as f:
    long_description = f.read()

setup(
    name="pulp-cookbook",
    version="0.1.0b10.dev",
    description="Cookbook plugin for the Pulp Project",
    long_description=long_description,
    author="Simon Baatz",
    author_email="gmbnomis@gmail.com",
    url="https://github.com/pulp/pulp_cookbook/",
    install_requires=requirements,
    include_package_data=True,
    packages=find_packages(exclude=["test"]),
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={"pulpcore.plugin": ["pulp_cookbook = pulp_cookbook:default_app_config"]},
)
