#!/usr/bin/env python3

from setuptools import setup, find_packages

requirements = [
    'pulpcore-plugin>=0.1.0b2',
]

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='pulp-cookbook',
    version='0.0.1a1',
    description='Cookbook plugin for the Pulp Project',
    long_description=long_description,
    author='Simon Baatz',
    author_email='gmbnomis@gmail.com',
    url='https://github.com/gmbnomis/pulp_cookbook/',
    install_requires=requirements,
    include_package_data=True,
    packages=find_packages(exclude=['test']),
    entry_points={
        'pulpcore.plugin': [
            'pulp_cookbook = pulp_cookbook:default_app_config',
        ]
    }
)
