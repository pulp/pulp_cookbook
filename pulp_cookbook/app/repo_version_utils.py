# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.db.models import Count

from pulp_cookbook.app.models import CookbookPackageContent


def check_repo_version_constraint(repository_version):
    """
    Ensure that repo version fulfills repo_key_fields uniqueness.

    Raises:
        ValueError: When constraint is violated

    """
    fields = CookbookPackageContent.repo_key_fields
    qs_content = CookbookPackageContent.objects.filter(pk__in=repository_version.content)
    qs = qs_content.values(*fields).annotate(num_cookbooks=Count("pk")).filter(num_cookbooks__gt=1)
    duplicates = [f"{res['name']} {res['version']}" for res in qs]
    if duplicates:
        duplicates_str = ", ".join(duplicates)
        raise ValueError(
            f"repository version would contain multiple versions of cookbooks: {duplicates_str}"
        )
