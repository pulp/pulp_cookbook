# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests that publish cookbook plugin repositories."""
import unittest
from random import choice
from urllib.parse import urljoin

from requests.exceptions import HTTPError

from pulp_smash import api, config
from pulp_smash.exceptions import TaskReportError
from pulp_smash.pulp3.constants import REPO_PATH
from pulp_smash.pulp3.utils import (
    delete_orphans,
    gen_remote,
    gen_repo,
    get_versions,
    publish,
    sync,
)

from pulp_cookbook.tests.functional.api.utils import gen_publisher, get_cookbook_content
from pulp_cookbook.tests.functional.constants import (
    fixture_u1,
    fixture_u1_diff_digest,
    COOKBOOK_REMOTE_PATH,
    COOKBOOK_PUBLISHER_PATH,
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
        2. Create a publication by supplying the latest ``repository_version``.
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
        self.addCleanup(client.delete, remote["_href"])

        repo = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo["_href"])

        sync(cfg, remote, repo)
        repo = client.get(repo["_href"])
        repo_content = get_cookbook_content(repo)
        self.assertTrue(repo_content)

        publisher = client.post(COOKBOOK_PUBLISHER_PATH, gen_publisher())
        self.addCleanup(client.delete, publisher["_href"])

        # Step 1
        repo = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo["_href"])
        for cookbook in repo_content:
            client.post(
                repo["_versions_href"], {"add_content_units": [cookbook["_href"]]}
            )
        version_hrefs = tuple(ver["_href"] for ver in get_versions(repo))
        non_latest = choice(version_hrefs[:-1])

        # Step 2
        publication = publish(cfg, publisher, repo)

        # Step 3
        self.assertEqual(publication["repository_version"], version_hrefs[-1])

        # Step 4
        publication = publish(cfg, publisher, repo, non_latest)

        # Step 5
        self.assertEqual(publication["repository_version"], non_latest)

        # Step 6
        with self.assertRaises(HTTPError):
            body = {"repository": repo["_href"], "repository_version": non_latest}
            client.post(urljoin(publisher["_href"], "publish/"), body)


class RepoVersionConstraintValidationTestCase(unittest.TestCase):
    """Test the check for repo version constraints."""

    def test_publish_invalid_repo_version(self):
        """Repo version containing two units with the same name and version can't be published."""
        cfg = config.get_config()
        delete_orphans(cfg)
        client = api.Client(cfg, api.json_handler)

        # Create repo u1 and sync partially
        repo_u1 = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo_u1["_href"])

        body = gen_remote(fixture_u1.url, cookbooks={fixture_u1.example1_name: ""})
        remote_u1 = client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote_u1["_href"])

        sync(cfg, remote_u1, repo_u1)
        repo_u1 = client.get(repo_u1["_href"])

        # Create repo u1_diff_digest and sync partially
        repo_u1_diff_digest = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo_u1_diff_digest["_href"])

        body = gen_remote(
            fixture_u1_diff_digest.url, cookbooks={fixture_u1.example1_name: ""}
        )
        remote_u1_diff_digest = client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote_u1_diff_digest["_href"])

        sync(cfg, remote_u1_diff_digest, repo_u1_diff_digest)
        repo_u1_diff_digest = client.get(repo_u1_diff_digest["_href"])

        # Add a content unit from u1_diff_digest to u1 (duplicate name&version)
        content_u1_diff_digest = get_cookbook_content(repo_u1_diff_digest)
        self.assertTrue(content_u1_diff_digest)
        client.post(
            repo_u1["_versions_href"],
            {"add_content_units": [content_u1_diff_digest[0]["_href"]]},
        )

        publisher = client.post(COOKBOOK_PUBLISHER_PATH, gen_publisher())
        self.addCleanup(client.delete, publisher["_href"])
        with self.assertRaisesRegex(TaskReportError, "would contain multiple versions"):
            publish(cfg, publisher, repo_u1)
