# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from unittest.mock import Mock

from django.db import connection, reset_queries
from django.test import TestCase
from django.test.utils import override_settings

from pulpcore.plugin.models import ContentArtifact, PublishedArtifact

from pulp_cookbook.app.models import CookbookPackageContent, CookbookPublication, CookbookRepository
from pulp_cookbook.app.repo_version_utils import check_repo_version_constraint
from pulp_cookbook.app.tasks.publishing import populate


class CheckRepoVersionConstraintTestCase(TestCase):
    """Verify check_repo_version_constraint() method."""

    def new_version_content(self):
        repository_version = Mock()
        repository_version.content = CookbookPackageContent.objects.all()
        repository_version.repository.CONTENT_TYPES = [CookbookPackageContent]
        return repository_version

    def test_check_repo_version_constraint_ok(self):
        CookbookPackageContent.objects.create(
            name="c1", version="1.0.0", content_id_type="sha256", content_id="1", dependencies={}
        )
        CookbookPackageContent.objects.create(
            name="c2", version="1.0.0", content_id_type="sha256", content_id="1", dependencies={}
        )
        CookbookPackageContent.objects.create(
            name="c1", version="1.0.1", content_id_type="sha256", content_id="2", dependencies={}
        )

        check_repo_version_constraint(self.new_version_content())

    def test_check_repo_version_constraint_not_ok(self):
        CookbookPackageContent.objects.create(
            name="c1", version="1.0.0", content_id_type="sha256", content_id="1", dependencies={}
        )
        CookbookPackageContent.objects.create(
            name="c1", version="1.0.0", content_id_type="sha256", content_id="2", dependencies={}
        )
        CookbookPackageContent.objects.create(
            name="c2", version="1.0.0", content_id_type="sha256", content_id="1", dependencies={}
        )
        CookbookPackageContent.objects.create(
            name="c2", version="1.0.0", content_id_type="sha256", content_id="2", dependencies={}
        )
        CookbookPackageContent.objects.create(
            name="c1", version="1.0.1", content_id_type="sha256", content_id="1", dependencies={}
        )
        with self.assertRaisesRegex(
            ValueError,
            r"contain multiple versions of cookbooks: (c1 1.0.0, c2 1.0.0|c2 1.0.0, c1 1.0.0)",
        ):
            check_repo_version_constraint(self.new_version_content())

    def test_check_repo_version_constraint_same_and_different_id_types_not_ok(self):
        CookbookPackageContent.objects.create(
            name="c1", version="1.0.0", content_id_type="sha256", content_id="1", dependencies={}
        )
        CookbookPackageContent.objects.create(name="c1", version="1.0.0", dependencies={})
        CookbookPackageContent.objects.create(
            name="c1", version="1.0.1", content_id_type="sha256", content_id="2", dependencies={}
        )

        with self.assertRaisesRegex(ValueError, "would contain multiple versions of cookbooks"):
            check_repo_version_constraint(self.new_version_content())


class CheckPublishingPopulate(TestCase):
    """Verify populate() from the publishing task."""

    def setUp(self):
        """Setup 20 content units with an associated ContentArtifact."""
        self.repository = CookbookRepository.objects.create()
        self.content_count = 20
        for i in range(self.content_count):
            c_i = CookbookPackageContent.objects.create(
                name="cookbook", version=f"{i}.0.0", dependencies={}
            )
            ContentArtifact.objects.create(
                artifact=None, content=c_i, relative_path=c_i.relative_path()
            )
        with self.repository.new_version() as self.version1:
            self.version1.add_content(CookbookPackageContent.objects.all())

    @override_settings(DEBUG=True)  # Set DEBUG to record connection.queries
    def test_populate_db_ops(self):
        """Sanity check for the number of DB operations and records created."""
        publication = CookbookPublication.objects.create(repository_version=self.version1)
        reset_queries()
        entries = list(populate(publication, batch_size=int(self.content_count / 2) + 1))

        # 1 query for content count (batch_qs generator) -> 2 batches
        # 2 for content
        # 2 for content_artifact prefetch
        # 2 for bulk create of published artifacts
        self.assertLessEqual(
            len(connection.queries), 7, msg=f"More than 7 queries:\n {connection.queries}"
        )
        self.assertEqual(len(entries), self.content_count)
        self.assertEqual(PublishedArtifact.objects.count(), self.content_count)
