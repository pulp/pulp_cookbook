# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests that perform actions over content unit."""
import unittest

from requests.exceptions import HTTPError

from pulp_smash import api, config, utils
from pulp_smash.pulp3.constants import ARTIFACTS_PATH
from pulp_smash.pulp3.utils import delete_orphans

from pulp_cookbook.tests.functional.constants import fixture_u1, COOKBOOK_CONTENT_PATH


def _gen_content_unit_attrs(artifact, name):
    """Generate a dict with content unit attributes.

    :param: artifact: A dict of info about the artifact.
    :returns: A dict for use in creating a content unit.
    """
    return {"artifact": artifact["_href"], "name": name}


class ContentUnitTestCase(unittest.TestCase):
    """CRUD content unit.

    This test targets the following issues:

    * `Pulp #2872 <https://pulp.plan.io/issues/2872>`_
    * `Pulp #3445 <https://pulp.plan.io/issues/3445>`_
    * `Pulp Smash #870 <https://github.com/PulpQE/pulp-smash/issues/870>`_
    """

    @classmethod
    def setUpClass(cls):
        """Create class-wide variable."""
        cls.cfg = config.get_config()
        delete_orphans(cls.cfg)
        cls.content_unit = {}
        cls.client = api.Client(cls.cfg, api.json_handler)
        download_url = fixture_u1.cookbook_download_url(
            fixture_u1.example1_name, fixture_u1.example1_version
        )
        cookbooks = {"file": utils.http_get(download_url)}
        cls.artifact = cls.client.post(ARTIFACTS_PATH, files=cookbooks)

    @classmethod
    def tearDownClass(cls):
        """Clean class-wide variable."""
        delete_orphans(cls.cfg)

    def test_01_create_content_unit(self):
        """Create content unit."""
        attrs = _gen_content_unit_attrs(self.artifact, fixture_u1.example1_name)
        self.content_unit.update(self.client.post(COOKBOOK_CONTENT_PATH, attrs))
        for key, val in attrs.items():
            with self.subTest(key=key):
                self.assertEqual(self.content_unit[key], val)
        with self.subTest(key="content_id"):
            self.assertEqual(self.content_unit["content_id"], self.artifact["sha256"])

    def test_02_read_content_unit(self):
        """Read a content unit by its href."""
        content_unit = self.client.get(self.content_unit["_href"])
        for key, val in self.content_unit.items():
            with self.subTest(key=key):
                self.assertEqual(content_unit[key], val)

    def test_02_read_content_units(self):
        """Read content units by its name and version."""
        page = self.client.get(
            COOKBOOK_CONTENT_PATH,
            params={"name": self.content_unit["name"], "version": self.content_unit["version"]},
        )
        self.assertEqual(len(page["results"]), 1)
        for key, val in self.content_unit.items():
            with self.subTest(key=key):
                self.assertEqual(page["results"][0][key], val)

    def test_03_partially_update(self):
        """Attempt to update a content unit using HTTP PATCH.

        This HTTP method is not supported and a HTTP exception is expected.
        """
        attrs = _gen_content_unit_attrs(self.artifact, fixture_u1.example1_name)
        with self.assertRaises(HTTPError) as exc:
            self.client.patch(self.content_unit["_href"], attrs)
        self.assertEqual(exc.exception.response.status_code, 405)

    def test_03_fully_update(self):
        """Attempt to update a content unit using HTTP PUT.

        This HTTP method is not supported and a HTTP exception is expected.
        """
        attrs = _gen_content_unit_attrs(self.artifact, fixture_u1.example1_name)
        with self.assertRaises(HTTPError) as exc:
            self.client.put(self.content_unit["_href"], attrs)
        self.assertEqual(exc.exception.response.status_code, 405)

    def test_04_delete(self):
        """Attempt to delete a content unit using HTTP DELETE.

        This HTTP method is not supported and a HTTP exception is expected.
        """
        with self.assertRaises(HTTPError) as exc:
            self.client.delete(self.content_unit["_href"])
        self.assertEqual(exc.exception.response.status_code, 405)

    def test_05_create_content_unit_without_artifact(self):
        """Create content unit without an artifact."""
        attrs = {"name": "no_artifact", "artifact": None}
        with self.assertRaises(HTTPError) as exc:
            self.client.post(COOKBOOK_CONTENT_PATH, attrs)
        self.assertEqual(exc.exception.response.status_code, 400)


# TODO: implement
class DuplicateContentUnit(unittest.TestCase):
    """
    Attempt to create a duplicate content unit.

    This test targets the following issues:
    *  `Pulp #4125 <https://pulp.plan.io/issues/4125>`_
    """

    pass
