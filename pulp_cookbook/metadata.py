# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import tarfile
import json


class CookbookMetadata:
    """
    Represents metadata extracted from a cookbook tar archive.

    Attributes:
        metadata (dict): content of the 'metadata.json' file of a cookbook
    """

    def __init__(self, metadata):
        self.metadata = metadata

    @property
    def name(self):
        return self.metadata['name']

    @property
    def version(self):
        return self.metadata['version']

    @property
    def dependencies(self):
        return self.metadata['dependencies']

    @classmethod
    def from_cookbook_file(cls, file_name, name):
        """
        Construct a CookbookMetadata instance from a cookbook tar archive.

        Args:
            file_name (str): filename of the cookbook tar archive
            name (str): name of the cookbook ("metadata.json" file
                        is expected to be in the directoy `<name>`)

        Returns:
            CookbookMetadata: Instance containing the extracted metadata
        """
        tf = tarfile.open(file_name)
        for element in tf:
            if element.isfile() and element.name == name + '/metadata.json':
                metadata = json.load(tf.extractfile(element))
                # TODO: check name consistency, raise error
                return CookbookMetadata(metadata)
        raise FileNotFoundError


class Entry:
    """
    Universe entry: info about a cookbook in the universe file.


    Attributes:
        name (str): cookbook name
        version (str): cookbook version
        download_url (str): URL of cookbook tar package
        dependencies (dict): cookbook dependencies
    """

    def __init__(self, name, version, download_url, dependencies):
        """
        Args:
        """
        self.name = name
        self.version = version
        self.download_url = download_url
        self.dependencies = dependencies

    @property
    def data(self):
        return {
            'location_type': 'uri',
            'location_path': self.download_url,
            'download_url': self.download_url,
            'dependencies': self.dependencies
        }


class Universe:
    """
    Represents the cookbook universe.
    Describes cookbooks contained within the directory.

    Attributes:
        relative_path (str): An relative path to the universe.
    """

    def __init__(self, relative_path):
        """
        Args:
            relative_path (str): An relative path to the universe.
        """
        self.relative_path = relative_path

    def read(self):
        """
        Read the universe file at `relative_path` and yield cookbook entries.

        Yields: Entry: for each cookbook.
        """
        with open(self.relative_path) as fp:
            universe = json.load(fp)
        for cookbook_name, cookbook_versions in universe.items():
            for cookbook_version, cookbook_meta in cookbook_versions.items():
                yield Entry(cookbook_name, cookbook_version,
                            cookbook_meta['download_url'], cookbook_meta['dependencies'])

    def write(self, entries):
        """
        Write the universe JSON file.

        Args:
            entries (iterable): The entries to be written.
        """
        universe = dict()
        for entry in entries:
            try:
                versions = universe[entry.name]
            except KeyError:
                universe[entry.name] = versions = dict()
            versions[entry.version] = entry.data
        with open(self.relative_path, 'w+') as fp:
            json.dump(universe, fp)
