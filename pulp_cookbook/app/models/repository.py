# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.db.models import JSONField
from pulpcore.plugin.models import Remote, Repository

from pulp_cookbook.app.models.content import CookbookPackageContent
from pulp_cookbook.app.repo_version_utils import check_repo_version_constraint


class CookbookRemote(Remote):
    """
    Remote for "cookbook" content.
    """

    TYPE = "cookbook"

    cookbooks = JSONField(null=True)

    def specifier_cookbook_names(self):
        if self.cookbooks is None:
            return None
        else:
            return set(self.cookbooks.keys())

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class CookbookRepository(Repository):
    """
    The "cookbook" repository type.
    """

    TYPE = "cookbook"
    CONTENT_TYPES = [CookbookPackageContent]
    REMOTE_TYPES = [CookbookRemote]

    def finalize_new_version(self, new_version):
        """
        Ensure no added content contains the same `relative_path` as other content.

        Args:
            new_version (pulpcore.app.models.RepositoryVersion): The incomplete RepositoryVersion to
                finalize.
        Raises:
            ValueError: When constraint is violated

        """
        check_repo_version_constraint(new_version)

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
