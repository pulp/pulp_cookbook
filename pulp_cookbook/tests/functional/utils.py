# coding=utf-8
"""Utilities for tests for the cookbook plugin."""
from functools import partial
from unittest import SkipTest

from pulp_smash import api, selectors
from pulp_smash.pulp3.constants import REPO_PATH
from pulp_smash.pulp3.utils import (
    gen_remote,
    gen_repo,
    require_pulp_3,
    require_pulp_plugins,
    sync,
)

from pulp_cookbook.tests.functional.constants import (
    COOKBOOK_CONTENT_PATH,
    fixture_u1,
    COOKBOOK_REMOTE_PATH
)


def populate_pulp(cfg, url=None):
    """Add cookbook contents to Pulp.

    :param pulp_smash.config.PulpSmashConfig: Information about a Pulp
        application.
    :param url: The URL to a cookbook repository. Defaults
        to :data:`pulp_smash.constants.fixture_u1.url`.
    :returns: A list of dicts, where each dict describes one cookbook content in
        Pulp.
    """
    if url is None:
        url = fixture_u1.url
    client = api.Client(cfg, api.json_handler)
    remote = {}
    repo = {}
    try:
        remote.update(client.post(COOKBOOK_REMOTE_PATH, gen_remote(url)))
        repo.update(client.post(REPO_PATH, gen_repo()))
        sync(cfg, remote, repo)
    finally:
        if remote:
            client.delete(remote['_href'])
        if repo:
            client.delete(repo['_href'])
    return client.get(COOKBOOK_CONTENT_PATH)['results']


def set_up_module():
    """Skip tests Pulp 3 isn't under test or if pulp-cookbook isn't installed."""
    require_pulp_3(SkipTest)
    require_pulp_plugins({'pulp_cookbook'}, SkipTest)


skip_if = partial(selectors.skip_if, exc=SkipTest)  # pylint:disable=invalid-name
"""The ``@skip_if`` decorator, customized for unittest.

:func:`pulp_smash.selectors.skip_if` is test runner agnostic. This function is
identical, except that ``exc`` has been set to ``unittest.SkipTest``.
"""
