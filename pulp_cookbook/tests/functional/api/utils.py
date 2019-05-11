# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Utilities for cookbook plugin tests."""
import functools
from unittest import SkipTest

from pulp_smash import api, selectors
from pulp_smash.pulp3.utils import get_added_content, get_content, get_removed_content

from pulp_cookbook.tests.functional.constants import (
    COOKBOOK_CONTENT_NAME,
    COOKBOOK_PUBLICATION_PATH,
)


def _filter_for_cookbook_content(get_func, *args, **kwargs):
    content = get_func(*args, **kwargs)
    assert not content or list(content.keys()) == [COOKBOOK_CONTENT_NAME]
    return content.get(COOKBOOK_CONTENT_NAME, {})


get_cookbook_content = functools.partial(_filter_for_cookbook_content, get_content)
get_cookbook_added_content = functools.partial(_filter_for_cookbook_content, get_added_content)
get_cookbook_removed_content = functools.partial(_filter_for_cookbook_content, get_removed_content)


def get_content_and_unit_paths(repo):
    """Return the publication relative path of content units present in a cookbook repository.

    :param repo: A dict of information about the repository.
    :returns: A list of tuples (content unit, publication path of the unit) present in a given
              repository.
    """
    # The "relative_path" is actually a file path and name
    def rel_path(content):
        path_format = "cookbook_files/{0}/{2}/{0}-{1}.tar.gz"
        return path_format.format(
            content["name"], content["version"], content["version"].replace(".", "_")
        )

    return [(cu, rel_path(cu)) for cu in get_cookbook_content(repo)]


def create_publication(cfg, repo, version_href=None):
    """Create a cookbook publication.

    :param pulp_smash.config.PulpSmashConfig cfg: Information about the Pulp
        host.
    :param repo: A dict of information about the repository.
    :param version_href: A href for the repo version to be published.
    :returns: A publication. A dict of information about the just created
        publication.
    """
    if version_href:
        body = {"repository_version": version_href}
    else:
        body = {"repository": repo["_href"]}

    client = api.Client(cfg, api.json_handler)
    call_report = client.post(COOKBOOK_PUBLICATION_PATH, body)
    tasks = tuple(api.poll_spawned_tasks(cfg, call_report))
    return client.get(tasks[-1]["created_resources"][0])


skip_if = functools.partial(selectors.skip_if, exc=SkipTest)  # pylint:disable=invalid-name
"""The ``@skip_if`` decorator, customized for unittest.

:func:`pulp_smash.selectors.skip_if` is test runner agnostic. This function is
identical, except that ``exc`` has been set to ``unittest.SkipTest``.
"""
