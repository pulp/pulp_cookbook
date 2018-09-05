# coding=utf-8
"""Tests that sync cookbook plugin repositories."""
import unittest
from random import randint
from urllib.parse import urlsplit

from pulp_smash import api, config
from pulp_smash.pulp3.constants import REPO_PATH
from pulp_smash.pulp3.utils import (
    delete_orphans,
    gen_remote,
    gen_repo,
    get_added_content,
    get_content,
    get_removed_content,
    sync,
)

from pulp_cookbook.tests.functional.constants import (
    fixture_u1,
    COOKBOOK_REMOTE_PATH
)
from pulp_cookbook.tests.functional.utils import set_up_module as setUpModule  # noqa:F401


class SyncCookbookRepoTestCase(unittest.TestCase):
    """Sync repositories with the cookbook plugin."""

    @classmethod
    def setUpClass(cls):
        """Create class-wide variables."""
        cls.cfg = config.get_config()

    def verify_counts(self, repo, all_count, added_count, removed_count):
        self.assertEqual(len(get_content(repo)), all_count)
        self.assertEqual(len(get_added_content(repo)), added_count)
        self.assertEqual(len(get_removed_content(repo)), removed_count)

    def sync_and_inspect_task_report(self, remote, repo, download_count, mirror=None):
        """Do a sync and verify the number of downloaded artifacts.

        Returns:
            Task report structure
        """
        if mirror is None:
            sync_resp = sync(self.cfg, remote, repo)
        else:
            sync_resp = sync(self.cfg, remote, repo, mirror=mirror)
        tasks = tuple(api.poll_spawned_tasks(self.cfg, sync_resp))
        self.assertEqual(len(tasks), 1)
        for report in tasks[0]['progress_reports']:
            if report['message'] == "Downloading Artifacts":
                report['done'] == download_count
                report['total'] == download_count
        return tasks[0]

    def test_sync(self):
        """Sync repositories with the cookbook plugin.

        In order to sync a repository a remote has to be associated within
        this repository. When a repository is created this version field is set
        as None. After a sync the repository version is updated.

        Do the following:

        1.  Delete orphan content units, create a repository, and an remote.
        2.  Assert that repository version is None
        3.  Sync the remote.
        4.  Assert that repository version is not None and the artifact/content counts
        5.  Sync the remote one more time.
        6.  Assert that repository version is different from the previous one. Assert that no
            artifact was downloaded.
        7.  Add a filter for a single cookbook name to the remote.
        8.  Sync the remote.
        9.  Assert artifact/content counts
        10. Change the filter for a single cookbook name in the remote.
        11. Sync the remote with "mirror=False".
        12. Assert artifact/content counts (content must have been added)
        """
        delete_orphans(self.cfg)

        client = api.Client(self.cfg, api.json_handler)

        repo = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo['_href'])

        body = gen_remote(fixture_u1.url)
        remote = client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote['_href'])

        # Sync the full repository.
        self.assertIsNone(repo['_latest_version_href'])

        all_cookbook_count = fixture_u1.cookbook_count()
        task = self.sync_and_inspect_task_report(remote, repo, all_cookbook_count)

        repo = client.get(repo['_href'])
        latest_version_href = repo['_latest_version_href']
        self.assertIsNotNone(latest_version_href)
        self.assertEqual(latest_version_href,
                         task['created_resources'][0])
        self.verify_counts(repo,
                           all_cookbook_count, all_cookbook_count, 0)

        # Sync the full repository again.
        self.sync_and_inspect_task_report(remote, repo, 0)
        repo = client.get(repo['_href'])
        self.assertNotEqual(latest_version_href, repo['_latest_version_href'])
        self.verify_counts(repo, all_cookbook_count, 0, 0)

        # Sync the repository with a filter (mirror mode is the default).
        client.patch(remote['_href'], {'cookbooks': {fixture_u1.example1_name: ''}})
        self.sync_and_inspect_task_report(remote, repo, 0)
        repo = client.get(repo['_href'])
        self.assertNotEqual(latest_version_href, repo['_latest_version_href'])
        example1_count = fixture_u1.cookbook_count([fixture_u1.example1_name])
        self.verify_counts(repo,
                           example1_count,
                           0,
                           all_cookbook_count - example1_count)

        # Sync the repository with another filter and add cookbooks (mirror=False).
        client.patch(remote['_href'], {'cookbooks': {fixture_u1.example2_name: ''}})
        self.sync_and_inspect_task_report(remote, repo, 0, mirror=False)
        repo = client.get(repo['_href'])
        self.assertNotEqual(latest_version_href, repo['_latest_version_href'])
        self.verify_counts(repo,
                           fixture_u1.cookbook_count([fixture_u1.example1_name,
                                                      fixture_u1.example2_name]),
                           fixture_u1.cookbook_count([fixture_u1.example2_name]),
                           0)


class SyncChangeRepoVersionTestCase(unittest.TestCase):
    """Verify whether sync of repository updates repository version."""

    def test_all(self):
        """Verify whether the sync of a repository updates its version.

        This test explores the design choice stated in the `Pulp #3308`_ that a
        new repository version is created even if the sync does not add or
        remove any content units. Even without any changes to the remote if a
        new sync occurs, a new repository version is created.

        .. _Pulp #3308: https://pulp.plan.io/issues/3308

        Do the following:

        1. Create a repository, and an remote.
        2. Sync the repository an arbitrary number of times.
        3. Verify that the repository version is equal to the previous number
           of syncs.
        """
        cfg = config.get_config()
        client = api.Client(cfg, api.json_handler)

        repo = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo['_href'])

        body = gen_remote(fixture_u1.url)
        remote = client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote['_href'])

        number_of_syncs = randint(1, 10)
        for _ in range(number_of_syncs):
            sync(cfg, remote, repo)

        repo = client.get(repo['_href'])
        path = urlsplit(repo['_latest_version_href']).path
        latest_repo_version = int(path.split('/')[-2])
        self.assertEqual(latest_repo_version, number_of_syncs)
