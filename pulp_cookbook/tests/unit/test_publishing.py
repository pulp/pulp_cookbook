# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from unittest.mock import Mock

from django.test import TestCase

from pulp_cookbook.app.models import CookbookPackageContent
from pulp_cookbook.app.repo_version_utils import check_repo_version_constraint


class CheckRepoVersionConstraintTestCase(TestCase):
    """Verify check_repo_version_constraint() method."""

    def new_version_content(self):
        repository_version = Mock()
        repository_version.content = CookbookPackageContent.objects.all()
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
        with self.assertRaises(ValueError):
            check_repo_version_constraint(self.new_version_content())

    def test_check_repo_version_constraint_same_and_different_id_types_not_ok(self):
        CookbookPackageContent.objects.create(
            name="c1", version="1.0.0", content_id_type="sha256", content_id="1", dependencies={}
        )
        CookbookPackageContent.objects.create(name="c1", version="1.0.0", dependencies={})
        CookbookPackageContent.objects.create(
            name="c1", version="1.0.1", content_id_type="sha256", content_id="2", dependencies={}
        )

        with self.assertRaises(ValueError):
            check_repo_version_constraint(self.new_version_content())
