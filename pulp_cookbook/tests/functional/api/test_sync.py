# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests that sync cookbook plugin repositories."""
import unittest

from pulp_smash import api, config
from pulp_smash.exceptions import TaskReportError
from pulp_smash.pulp3.constants import IMMEDIATE_DOWNLOAD_POLICIES, ON_DEMAND_DOWNLOAD_POLICIES
from pulp_smash.pulp3.constants import REPO_PATH
from pulp_smash.pulp3.utils import delete_orphans, gen_remote, gen_repo, sync

from pulp_cookbook.tests.functional.constants import (
    fixture_u1,
    fixture_u1_diff_digest,
    COOKBOOK_REMOTE_PATH,
    DOWNLOAD_POLICIES,
)
from pulp_cookbook.tests.functional.api.utils import (
    get_cookbook_added_content,
    get_cookbook_content,
    get_cookbook_removed_content,
    sync_raw,
)


class SyncCookbookRepoTestCase(unittest.TestCase):
    """Sync repositories with the cookbook plugin."""

    @classmethod
    def setUpClass(cls):
        """Create class-wide variables."""
        cls.cfg = config.get_config()

    def setUp(self):
        delete_orphans(self.cfg)

    def verify_counts(self, repo, all_count, added_count, removed_count):
        self.assertEqual(len(get_cookbook_content(repo)), all_count)
        self.assertEqual(len(get_cookbook_added_content(repo)), added_count)
        self.assertEqual(len(get_cookbook_removed_content(repo)), removed_count)

    def verify_ids_and_artifacts(self, repo, policy):
        """
        Verify that content_id and artifact presence corresponds to the policy.

        Verify that cookbook content_id is of the right type (based in the
        format; content_type_id is hidden by the serializer). Artifacts must be
        present in 'immediate' mode, otherwise not.
        """
        for cookbook in get_cookbook_content(repo):
            if policy == "immediate":
                self.assertEqual(
                    len(cookbook["content_id"]),
                    64,
                    msg=f"{cookbook} does not have a SHA256 content_id",
                )
                self.assertIsNotNone(cookbook["_artifact"])
            else:
                self.assertEqual(
                    len(cookbook["content_id"]),
                    36,
                    msg=f"{cookbook} does not have a UUID conten_id",
                )
                self.assertIsNone(cookbook["_artifact"])

    def sync_and_inspect_task_report(
        self, remote, repo, download_count, mirror=None, policy="immediate"
    ):
        """Do a sync and verify the number of downloaded artifacts.

        Returns:
            Task report structure

        """
        if mirror is None:
            sync_resp = sync_raw(self.cfg, remote, repo)
        else:
            sync_resp = sync_raw(self.cfg, remote, repo, mirror=mirror)
        tasks = tuple(api.poll_spawned_tasks(self.cfg, sync_resp))
        self.assertEqual(len(tasks), 1)
        for report in tasks[0]["progress_reports"]:
            if report["message"] == "Downloading Artifacts":
                if policy != "immediate":
                    self.fail(f"'Downloading Artifacts' stage in task report for {policy} policy")
                self.assertEqual(report["done"], download_count)
                break
        else:
            if policy == "immediate":
                self.fail("Could not find 'Downloading Artifacts' stage in task report")
        return tasks[0]

    def do_create_repo_and_sync(self, client, policy):
        """
        Create a repo and remote (fixture_u1) using `policy`. Sync the repo.

        Verify that a new version was created, the number of downloads and the
        number of content units.
        """
        repo = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo["_href"])

        body = gen_remote(fixture_u1.url, policy=policy)
        remote = client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote["_href"])

        # Sync the full repository.
        self.assertIsNone(repo["_latest_version_href"])

        all_cookbook_count = fixture_u1.cookbook_count()
        task = self.sync_and_inspect_task_report(remote, repo, all_cookbook_count, policy=policy)

        repo = client.get(repo["_href"])

        latest_version_href = repo["_latest_version_href"]
        self.assertIsNotNone(latest_version_href)
        self.assertEqual(latest_version_href, task["created_resources"][0])
        self.verify_counts(repo, all_cookbook_count, all_cookbook_count, 0)

        return repo, remote

    def do_create_repo_and_sync_twice(self, client, policy, second_policy):
        """
        Create a repo and remote (fixture_u1). Sync the repo twice.

        The first sync happens with policy `policy`, the second sync with policy
        `second_policy`.

        Verify that a new version was created, the number of downloads and the
        number of content units for both syncs.
        """
        all_cookbook_count = fixture_u1.cookbook_count()

        repo, remote = self.do_create_repo_and_sync(client, policy)
        latest_version_href = repo["_latest_version_href"]

        body = gen_remote(fixture_u1.url, policy=second_policy)
        client.patch(remote["_href"], body)

        # Sync the full repository again using the second policy.
        exp_download_count = 0
        exp_policy = second_policy
        if policy != "immediate" and second_policy == "immediate":
            exp_download_count = all_cookbook_count
        if policy == "immediate":
            exp_policy = "immediate"
        self.sync_and_inspect_task_report(
            remote, repo, exp_download_count, policy=second_policy, mirror=True
        )
        repo = client.get(repo["_href"])
        self.assertNotEqual(latest_version_href, repo["_latest_version_href"])
        # When we download the actual artifacts, the respective content unit will be replaced.
        # This looks like adding/deleting all cookbooks.
        self.verify_counts(repo, all_cookbook_count, exp_download_count, exp_download_count)
        self.verify_ids_and_artifacts(repo, exp_policy)

        return repo, remote

    def do_sync_check(self, policy):
        """Sync repository with the cookbook plugin.

        In order to sync a repository a remote has to be associated within
        this repository. When a repository is created this version field is set
        as None. After a sync the repository version is updated.

        Do the following:

        1.  Delete orphan content units, create a repository, and an remote.
        2.  Assert that repository version is None
        3.  Sync the remote.
        4.  Assert that repository version is not None and the artifact/content counts
        5.  Add a filter for a single cookbook name to the remote.
        6.  Sync the remote.
        7.  Assert artifact/content counts
        8. Change the filter for a single cookbook name in the remote.
        9. Sync the remote with "mirror=False".
        10. Assert artifact/content counts (content must have been added)
        """
        client = api.Client(self.cfg, api.json_handler)

        repo, remote = self.do_create_repo_and_sync(client, policy)

        # Sync the repository with a filter (use mirror mode).
        all_cookbook_count = fixture_u1.cookbook_count()
        latest_version_href = repo["_latest_version_href"]

        client.patch(remote["_href"], {"cookbooks": {fixture_u1.example1_name: ""}})
        self.sync_and_inspect_task_report(remote, repo, 0, policy=policy, mirror=True)
        repo = client.get(repo["_href"])
        self.assertNotEqual(latest_version_href, repo["_latest_version_href"])
        example1_count = fixture_u1.cookbook_count([fixture_u1.example1_name])
        self.verify_counts(repo, example1_count, 0, all_cookbook_count - example1_count)

        # Sync the repository with another filter and add cookbooks (additive mode (default).
        client.patch(remote["_href"], {"cookbooks": {fixture_u1.example2_name: ""}})
        # Although cookbook content is already present, it is not present in the
        # repository. Thus, it must be downloaded again.
        example2_count = fixture_u1.cookbook_count([fixture_u1.example2_name])
        self.sync_and_inspect_task_report(remote, repo, example2_count, policy=policy)
        repo = client.get(repo["_href"])
        self.assertNotEqual(latest_version_href, repo["_latest_version_href"])
        self.verify_counts(
            repo,
            fixture_u1.cookbook_count([fixture_u1.example1_name, fixture_u1.example2_name]),
            fixture_u1.cookbook_count([fixture_u1.example2_name]),
            0,
        )

        # Verify that cookbook content_id is of the right type (content_type_id
        # is hidden by the serializer)
        self.verify_ids_and_artifacts(repo, policy)

    def test_sync_immediate(self):
        self.do_sync_check("immediate")

    def test_sync_on_demand(self):
        self.do_sync_check("on_demand")

    def test_sync_streamed(self):
        self.do_sync_check("streamed")

    def test_sync_immediate_immediate(self):
        client = api.Client(self.cfg, api.json_handler)
        self.do_create_repo_and_sync_twice(client, "immediate", "immediate")

    def test_sync_on_demand_immediate(self):
        client = api.Client(self.cfg, api.json_handler)
        self.do_create_repo_and_sync_twice(client, "on_demand", "immediate")

    def test_sync_immediate_on_demand(self):
        client = api.Client(self.cfg, api.json_handler)
        self.do_create_repo_and_sync_twice(client, "immediate", "on_demand")

    def test_sync_on_demand_on_demand(self):
        client = api.Client(self.cfg, api.json_handler)
        self.do_create_repo_and_sync_twice(client, "on_demand", "on_demand")

    def test_sync_repo_isolation(self):
        """Sync two repositories with same content but different artifacts.

        The two repo fixtures u1 and u1_diff_digest contain the same cookbooks
        by name and version, but differ in the digest of the artifact. Ensure
        that syncing these two remotes to two repos respectively does not mixup
        cookbooks.
        """
        client = api.Client(self.cfg, api.json_handler)

        # Create repo u1 and sync partially
        repo_u1 = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo_u1["_href"])

        body = gen_remote(fixture_u1.url, cookbooks={fixture_u1.example1_name: ""})
        remote_u1 = client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote_u1["_href"])

        self.assertIsNone(repo_u1["_latest_version_href"])

        example1_count = fixture_u1.cookbook_count([fixture_u1.example1_name])
        self.sync_and_inspect_task_report(remote_u1, repo_u1, example1_count)

        repo_u1 = client.get(repo_u1["_href"])
        self.verify_counts(
            repo_u1, all_count=example1_count, added_count=example1_count, removed_count=0
        )

        # Create repo u1_diff_digest and do a full sync
        repo_u1_diff_digest = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo_u1_diff_digest["_href"])

        body = gen_remote(fixture_u1_diff_digest.url)
        remote_u1_diff_digest = client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote_u1_diff_digest["_href"])

        self.assertIsNone(repo_u1_diff_digest["_latest_version_href"])

        # u1 and u1_diff_digest must not share content: all cookbooks are added
        cookbook_count = fixture_u1_diff_digest.cookbook_count()
        self.sync_and_inspect_task_report(
            remote_u1_diff_digest, repo_u1_diff_digest, cookbook_count
        )

        repo_u1_diff_digest = client.get(repo_u1_diff_digest["_href"])
        self.verify_counts(
            repo_u1_diff_digest,
            all_count=cookbook_count,
            added_count=cookbook_count,
            removed_count=0,
        )

        # Full sync u1
        client.patch(remote_u1["_href"], {"cookbooks": {}})
        all_cookbook_count = fixture_u1.cookbook_count()
        self.sync_and_inspect_task_report(remote_u1, repo_u1, all_cookbook_count - example1_count)
        repo_u1 = client.get(repo_u1["_href"])
        self.verify_counts(
            repo_u1,
            all_count=all_cookbook_count,
            added_count=all_cookbook_count - example1_count,
            removed_count=0,
        )

        # Verify that the same cookbooks (w.r.t. name and version) differ by content_id
        content_u1_diff_digest = get_cookbook_content(repo_u1_diff_digest)
        self.assertTrue(content_u1_diff_digest)
        for c_u1 in get_cookbook_content(repo_u1):
            for c_u1_diff_digest in content_u1_diff_digest:
                if (
                    c_u1["name"] == c_u1_diff_digest["name"]
                    and c_u1["version"] == c_u1_diff_digest["version"]
                ):
                    artifact_u1 = client.get(c_u1["_artifact"])
                    self.assertEqual(c_u1["content_id"], artifact_u1["sha256"])
                    artifact_u1_diff_digest = client.get(c_u1_diff_digest["_artifact"])
                    self.assertEqual(
                        c_u1_diff_digest["content_id"], artifact_u1_diff_digest["sha256"]
                    )
                    self.assertNotEqual(c_u1["content_id"], c_u1_diff_digest["content_id"])
                    break
            else:
                self.fail(f"Found no matching cookbook for {c_u1} in u1_diff_digest")


class SyncInvalidTestCase(unittest.TestCase):
    """Sync a repository with an invalid given url on the remote."""

    @classmethod
    def setUpClass(cls):
        """Create class-wide variables."""
        cls.cfg = config.get_config()
        cls.client = api.Client(cls.cfg, api.json_handler)

    def test_invalid_url(self):
        """Sync a repository using a remote url that does not exist.

        Test that we get a task failure. See :meth:`do_test`.
        """
        context = self.do_test("http://example.com/invalid/")
        self.assertIsNotNone(context.exception.task["error"]["description"])

    def test_invalid_policies(self):
        """Sync a repository using all unsupported policies.

        Test that we get a task failure when using an unsupported policy. See
        :meth:`do_test`.
        """
        for policy in IMMEDIATE_DOWNLOAD_POLICIES + ON_DEMAND_DOWNLOAD_POLICIES:
            if policy not in DOWNLOAD_POLICIES:
                context = self.do_test(fixture_u1.url, policy=policy)
                self.assertIsNotNone(context.exception.task["error"]["description"])

    def do_test(self, url, **remote_kwargs):
        """Sync a repository given ``url`` on the remote."""
        repo = self.client.post(REPO_PATH, gen_repo())
        self.addCleanup(self.client.delete, repo["_href"])
        body = gen_remote(url=url, **remote_kwargs)
        remote = self.client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(self.client.delete, remote["_href"])
        with self.assertRaises(TaskReportError) as context:
            sync(self.cfg, remote, repo, mirror=True)
        return context
