# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.db.models import Count


def check_repo_version_constraint(repository_version):
    """
    Ensure that repo version fulfills repo_key_fields uniqueness.

    Raises:
        ValueError: When constraint is violated

    """
    assert repository_version.repository.CONTENT_TYPES
    for content_class in repository_version.repository.CONTENT_TYPES:
        fields = content_class.repo_key_fields
        if fields:
            qs_content = content_class.objects.filter(pk__in=repository_version.content)
            qs = (
                qs_content.values(*fields)
                .annotate(num_cookbooks=Count("pk"))
                .filter(num_cookbooks__gt=1)
            )
            duplicates = [f"{res['name']} {res['version']}" for res in qs]
            if duplicates:
                duplicates_str = ", ".join(duplicates)
                raise ValueError(
                    "repository version would contain multiple versions"
                    f" of cookbooks: {duplicates_str}"
                )
