#!/usr/bin/env python3

import codecs
import os
import re

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """Read file at joined parts (relative to the directory this file is in)."""
    with codecs.open(os.path.join(here, *parts), "r") as fp:
        return fp.read()


def find_version(*file_paths):
    """Find version variable value in given file."""
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open("README.rst") as f:
    long_description = f.read()

setup(
    name="pulp-cookbook",
    version=find_version("pulp_cookbook", "__init__.py"),
    description="Cookbook plugin for the Pulp Project",
    long_description=long_description,
    author="Simon Baatz",
    author_email="gmbnomis@gmail.com",
    url="https://github.com/gmbnomis/pulp_cookbook/",
    install_requires=["pulpcore-plugin~=0.1rc2"],
    extras_require={"postgres": ["pulpcore[postgres]"], "mysql": ["pulpcore[mysql]"]},
    include_package_data=True,
    packages=find_packages(exclude=["test"]),
    classifiers=(
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ),
    entry_points={"pulpcore.plugin": ["pulp_cookbook = pulp_cookbook:default_app_config"]},
)
