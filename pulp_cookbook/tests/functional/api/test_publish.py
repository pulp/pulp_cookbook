# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests that publish cookbook plugin repositories."""
import unittest
from random import choice

from requests.exceptions import HTTPError

from pulp_smash import api, config
from pulp_smash.pulp3.utils import (
    delete_orphans,
    gen_remote,
    gen_repo,
    get_versions,
    modify_repo,
    sync,
)

from pulp_cookbook.tests.functional.api.utils import create_publication, get_cookbook_content
from pulp_cookbook.tests.functional.constants import (
    fixture_u1,
    COOKBOOK_REMOTE_PATH,
    COOKBOOK_REPO_PATH,
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

        repo = client.post(COOKBOOK_REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo["pulp_href"])

        sync(cfg, remote, repo, mirror=True)
        repo = client.get(repo["pulp_href"])
        repo_content = get_cookbook_content(repo)
        self.assertTrue(repo_content)

        # Step 1
        repo = client.post(COOKBOOK_REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo["pulp_href"])
        for cookbook in repo_content:
            modify_repo(cfg, repo, add_units=[cookbook])

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
