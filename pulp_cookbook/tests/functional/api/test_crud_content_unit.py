# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests that perform actions over content unit."""
import hashlib
import unittest

from requests.exceptions import HTTPError

from pulp_smash import api, cli, config, exceptions, utils
from pulp_smash.pulp3.bindings import delete_orphans
from pulp_smash.pulp3.constants import ARTIFACTS_PATH
from pulp_smash.pulp3.utils import gen_repo

from pulp_cookbook.tests.functional.constants import (
    fixture_u1,
    COOKBOOK_CONTENT_PATH,
    COOKBOOK_REPO_PATH,
)


def _gen_content_unit_attrs(artifact, name):
    """Generate a dict with content unit attributes.

    :param: artifact: A dict of info about the artifact.
    :returns: A dict for use in creating a content unit.
    """
    return {"artifact": artifact["pulp_href"], "name": name}


def _gen_file_content_upload_attrs(name):
    """Generate a dict with content unit attributes without artifact for upload.

    :param name: name of the cookbook.
    :returns: A dict for use in creating a content unit from a file.
    """
    return {"name": name}


class CommonsForContentTestCases(unittest.TestCase):
    """Define common methods for setup/teardown & methods usable in tests."""

    @classmethod
    def setUpClass(cls):
        """Create class-wide variable."""
        cls.cfg = config.get_config()
        cls.cli_client = cli.Client(cls.cfg)
        delete_orphans()
        cls.content_unit = {}
        cls.client_task = api.Client(cls.cfg, api.task_handler)
        cls.client = api.Client(cls.cfg, api.json_handler)
        download_url = fixture_u1.cookbook_download_url(
            fixture_u1.example1_name, fixture_u1.example1_version
        )
        cls.cookbook_files = {"file": utils.http_get(download_url)}
        cls.cookbook_sha256 = hashlib.sha256(cls.cookbook_files["file"]).hexdigest()

    @classmethod
    def set_common_artifact(cls, artifact):
        """Store the artifact instance to be shared between test methods."""
        cls.artifact = artifact

    @classmethod
    def tearDownClass(cls):
        """Clean class-wide variable."""
        delete_orphans()

    def create_and_verify_content_unit_from_file(self, repo_href=None):
        """Create content unit from file."""
        attrs = _gen_file_content_upload_attrs(fixture_u1.example1_name)
        if repo_href:
            attrs["repository"] = repo_href
        resources = self.client_task.post(
            COOKBOOK_CONTENT_PATH, data=attrs, files=self.cookbook_files
        )
        api_root = utils.get_pulp_setting(self.cli_client, "API_ROOT")
        if repo_href:
            # We get back a list: the new content unit and the new repo version
            for resource in resources:
                if resource["pulp_href"].startswith(f"{api_root}api/v3/content/"):
                    self.content_unit.update(resource)
                else:
                    self.assertRegex(
                        resource["pulp_href"], f"^{api_root}api/v3/repositories/.*/versions/"
                    )
                    repo_version = resource
                    self.assertEqual(
                        repo_version["content_summary"]["added"]["cookbook.cookbook"]["count"], 1
                    )
                    self.assertEqual(
                        repo_version["content_summary"]["present"]["cookbook.cookbook"]["count"], 1
                    )
        else:
            self.content_unit.update(resources)
        for key, val in _gen_file_content_upload_attrs(fixture_u1.example1_name).items():
            with self.subTest(key=key):
                self.assertEqual(self.content_unit[key], val)
        with self.subTest(key="content_id"):
            self.assertEqual(self.content_unit["content_id"], self.cookbook_sha256)

        # Get the created artifact and store it for use in further tests
        artifact = self.client.get(self.content_unit["artifact"])
        self.assertEqual(artifact["sha256"], self.cookbook_sha256)
        self.set_common_artifact(artifact)

    def read_content_unit(self):
        """Read a content unit by its href."""
        content_unit = self.client.get(self.content_unit["pulp_href"])
        for key, val in self.content_unit.items():
            with self.subTest(key=key):
                self.assertEqual(content_unit[key], val)

    def read_content_units(self):
        """Read content units by its name and version."""
        page = self.client.get(
            COOKBOOK_CONTENT_PATH,
            params={"name": self.content_unit["name"], "version": self.content_unit["version"]},
        )
        self.assertEqual(len(page["results"]), 1)
        for key, val in self.content_unit.items():
            with self.subTest(key=key):
                self.assertEqual(page["results"][0][key], val)

    def partially_update(self):
        """Attempt to update a content unit using HTTP PATCH.

        This HTTP method is not supported and a HTTP exception is expected.
        """
        attrs = _gen_content_unit_attrs(self.artifact, fixture_u1.example1_name)
        with self.assertRaises(HTTPError) as exc:
            self.client.patch(self.content_unit["pulp_href"], attrs)
        self.assertEqual(exc.exception.response.status_code, 405)

    def fully_update(self):
        """Attempt to update a content unit using HTTP PUT.

        This HTTP method is not supported and a HTTP exception is expected.
        """
        attrs = _gen_content_unit_attrs(self.artifact, fixture_u1.example1_name)
        with self.assertRaises(HTTPError) as exc:
            self.client.put(self.content_unit["pulp_href"], attrs)
        self.assertEqual(exc.exception.response.status_code, 405)

    def delete(self):
        """Attempt to delete a content unit using HTTP DELETE.

        This HTTP method is not supported and a HTTP exception is expected.
        """
        with self.assertRaises(HTTPError) as exc:
            self.client.delete(self.content_unit["pulp_href"])
        self.assertEqual(exc.exception.response.status_code, 405)

    def create_content_unit_without_artifact(self):
        """Create content unit without an artifact."""
        attrs = {"name": "no_artifact", "artifact": None}
        with self.assertRaises(HTTPError) as exc:
            self.client.post(COOKBOOK_CONTENT_PATH, attrs)
        self.assertEqual(exc.exception.response.status_code, 400)


class ContentUnitTestCase(CommonsForContentTestCases):
    """CRUD content unit.

    This test targets the following issues:

    * `Pulp #2872 <https://pulp.plan.io/issues/2872>`_
    * `Pulp #3445 <https://pulp.plan.io/issues/3445>`_
    * `Pulp Smash #870 <https://github.com/PulpQE/pulp-smash/issues/870>`_
    """

    def test_01_create_content_unit(self):
        """Create content unit."""
        artifact = self.client.post(ARTIFACTS_PATH, files=self.cookbook_files)
        self.set_common_artifact(artifact)

        attrs = _gen_content_unit_attrs(artifact, fixture_u1.example1_name)
        self.content_unit.update(self.client_task.post(COOKBOOK_CONTENT_PATH, attrs))
        for key, val in attrs.items():
            with self.subTest(key=key):
                self.assertEqual(self.content_unit[key], val)
        with self.subTest(key="content_id"):
            self.assertEqual(self.content_unit["content_id"], artifact["sha256"])

    def test_02_read_content_unit(self):
        self.read_content_unit()

    def test_02_read_content_units(self):
        self.read_content_units()

    def test_03_partially_update(self):
        self.partially_update()

    def test_03_fully_update(self):
        self.fully_update()

    def test_04_delete(self):
        self.delete()

    def test_05_create_content_unit_without_artifact(self):
        self.create_content_unit_without_artifact()


class ContentUnitUploadTestCase(CommonsForContentTestCases):
    """Test Content generation using direct upload of a cookbook file."""

    def test_01_create_content_unit_from_file(self):
        self.create_and_verify_content_unit_from_file()

    def test_02_read_content_unit(self):
        self.read_content_unit()

    def test_02_read_content_units(self):
        self.read_content_units()

    def test_03_create_content_unit_from_same_file(self):
        with self.assertRaisesRegex(
            exceptions.TaskReportError, r"There is already a cookbook package"
        ):
            self.create_and_verify_content_unit_from_file()


class ContentUnitUploadNewRepoVersionTestCase(CommonsForContentTestCases):
    """Test Content generation using direct upload of a cookbook file."""

    def do_create_repo(self, client):
        """
        Create a repo.
        """
        repo = client.post(COOKBOOK_REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo["pulp_href"])
        return repo

    def test_01_create_content_unit(self):
        repo = self.do_create_repo(self.client)
        self.create_and_verify_content_unit_from_file(repo_href=repo["pulp_href"])

    def test_02_read_content_unit(self):
        self.read_content_unit()
