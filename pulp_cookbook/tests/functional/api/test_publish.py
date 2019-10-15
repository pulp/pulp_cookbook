# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests that publish cookbook plugin repositories."""
import unittest
from random import choice

from requests.exceptions import HTTPError

from pulp_smash import api, config
from pulp_smash.exceptions import TaskReportError
from pulp_smash.pulp3.constants import REPO_PATH
from pulp_smash.pulp3.utils import delete_orphans, gen_remote, gen_repo, get_versions, sync

from pulp_cookbook.tests.functional.api.utils import create_publication, get_cookbook_content
from pulp_cookbook.tests.functional.constants import (
    fixture_u1,
    fixture_u1_diff_digest,
    COOKBOOK_REMOTE_PATH,
    COOKBOOK_PUBLICATION_PATH,
)


class PublishAnyRepoVersionTestCase(unittest.TestCase):
    """Test whether a particular repository version can be published.

    This test targets the following issues:

    * `Pulp #3324 <https://pulp.plan.io/issues/3324>`_
    * `Pulp Smash #897 <https://github.com/PulpQE/pulp-smash/issues/897>`_
    """

    def test_all(self):
        """Test whether a particular repository version can be published.

        1. Create a repository with at least 2 repository versions.
        2. Create a publication without supplying a repository_version (i.e.
           take the latest ``repository_version``).
        3. Assert that the publication ``repository_version`` attribute points
           to the latest repository version.
        4. Create a publication by supplying the non-latest
           ``repository_version``.
        5. Assert that the publication ``repository_version`` attribute points
           to the supplied repository version.
        6. Assert that an exception is raised when providing two different
           repository versions to be published at same time.
        """
        cfg = config.get_config()

        delete_orphans(cfg)

        client = api.Client(cfg, api.json_handler)
        body = gen_remote(fixture_u1.url, cookbooks={fixture_u1.example1_name: ""})
        remote = client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote["pulp_href"])

        repo = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo["pulp_href"])

        sync(cfg, remote, repo, mirror=True)
        repo = client.get(repo["pulp_href"])
        repo_content = get_cookbook_content(repo)
        self.assertTrue(repo_content)

        # Step 1
        repo = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo["pulp_href"])
        for cookbook in repo_content:
            client.post(repo["versions_href"], {"add_content_units": [cookbook["pulp_href"]]})
        version_hrefs = tuple(ver["pulp_href"] for ver in get_versions(repo))
        non_latest = choice(version_hrefs[:-1])

        # Step 2
        publication = create_publication(cfg, repo)

        # Step 3
        self.assertEqual(publication["repository_version"], version_hrefs[-1])

        # Step 4
        publication = create_publication(cfg, repo, version_href=non_latest)

        # Step 5
        self.assertEqual(publication["repository_version"], non_latest)

        # Step 6
        with self.assertRaises(HTTPError):
            body = {"repository": repo["pulp_href"], "repository_version": non_latest}
            client.post(COOKBOOK_PUBLICATION_PATH, body)


class RepoVersionConstraintValidationTestCase(unittest.TestCase):
    """Test the check for repo version constraints."""

    def test_publish_invalid_repo_version(self):
        """Repo version containing two units with the same name and version can't be published."""
        cfg = config.get_config()
        delete_orphans(cfg)
        client = api.Client(cfg, api.json_handler)

        # Create repo u1 and sync partially
        repo_u1 = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo_u1["pulp_href"])

        body = gen_remote(fixture_u1.url, cookbooks={fixture_u1.example1_name: ""})
        remote_u1 = client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote_u1["pulp_href"])

        sync(cfg, remote_u1, repo_u1, mirror=True)
        repo_u1 = client.get(repo_u1["pulp_href"])

        # Create repo u1_diff_digest and sync partially
        repo_u1_diff_digest = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo_u1_diff_digest["pulp_href"])

        body = gen_remote(fixture_u1_diff_digest.url, cookbooks={fixture_u1.example1_name: ""})
        remote_u1_diff_digest = client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote_u1_diff_digest["pulp_href"])

        sync(cfg, remote_u1_diff_digest, repo_u1_diff_digest, mirror=True)
        repo_u1_diff_digest = client.get(repo_u1_diff_digest["pulp_href"])

        # Add a content unit from u1_diff_digest to u1 (duplicate name&version)
        content_u1_diff_digest = get_cookbook_content(repo_u1_diff_digest)
        self.assertTrue(content_u1_diff_digest)
        client.post(
            repo_u1["versions_href"],
            {"add_content_units": [content_u1_diff_digest[0]["pulp_href"]]},
        )

        with self.assertRaisesRegex(TaskReportError, "would contain multiple versions"):
            create_publication(cfg, repo_u1)
