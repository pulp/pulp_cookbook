# coding=utf-8
"""Tests that verify download of content served by Pulp."""
import hashlib
import unittest
from random import choice
from urllib.parse import urljoin

from pulp_smash import api, config, utils
from pulp_smash.pulp3.constants import DISTRIBUTION_PATH, REPO_PATH
from pulp_smash.pulp3.utils import (
    gen_distribution,
    gen_remote,
    gen_repo,
    publish,
    sync,
)

from pulp_cookbook.tests.functional.api.utils import (
    gen_publisher,
    get_content_and_unit_paths,
)
from pulp_cookbook.tests.functional.constants import (
    fixture_u1,
    COOKBOOK_REMOTE_PATH,
    COOKBOOK_PUBLISHER_PATH,
    COOKBOOK_BASE_LIVE_API_PATH,
)
from pulp_cookbook.tests.functional.utils import set_up_module as setUpModule  # noqa:F401


class DownloadContentTestCase(unittest.TestCase):
    """Verify whether content served by pulp can be downloaded."""

    def test_all(self):
        """Verify whether content served by pulp can be downloaded.

        The process of publishing content is more involved in Pulp 3 than it
        was under Pulp 2. Given a repository, the process is as follows:

        1. Create a publication from the repository. (The latest repository
           version is selected if no version is specified.) A publication is a
           repository version plus metadata.
        2. Create a distribution from the publication. The distribution defines
           at which URLs a publication is available. For the cookbook plugin
           this is below a live API at ``pulp_cookbook/market/`` e.g.
           ``http://example.com/pulp_cookbook/market/foo/`` and
           ``http://example.com/pulp_cookbook/market/bar/``.

        Do the following:

        1. Create, populate, publish, and distribute a repository.
        2. Select a random content unit in the distribution. Download that
           content unit from Pulp, and verify that the content unit has the
           same checksum when fetched directly from fixtures.

        This test targets the following issues:

        * `Pulp #2895 <https://pulp.plan.io/issues/2895>`_
        * `Pulp Smash #872 <https://github.com/PulpQE/pulp-smash/issues/872>`_
        """
        cfg = config.get_config()
        client = api.Client(cfg, api.json_handler)

        repo = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo['_href'])

        body = gen_remote(fixture_u1.url)
        remote = client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote['_href'])

        sync(cfg, remote, repo)
        repo = client.get(repo['_href'])

        # Create a publisher.
        publisher = client.post(COOKBOOK_PUBLISHER_PATH, gen_publisher())
        self.addCleanup(client.delete, publisher['_href'])

        # Create a publication.
        publication = publish(cfg, publisher, repo)
        self.addCleanup(client.delete, publication['_href'])

        # Create a distribution.
        body = gen_distribution()
        body['publication'] = publication['_href']
        distribution = client.post(DISTRIBUTION_PATH, body)
        self.addCleanup(client.delete, distribution['_href'])

        # pulp_cookbook universe live endpoint contains
        # all cookbooks
        distribution_base_url = cfg.get_hosts('api')[0].roles['api']['scheme']
        distribution_base_url += '://' + distribution['base_url'] + '/'

        api_host_cfg = cfg.get_hosts('api')[0]
        universe_url = api_host_cfg.roles['api']['scheme']
        universe_url += '://' + api_host_cfg.hostname
        universe_url += ':{}'.format(api_host_cfg.roles['api']['port'])
        universe_url += COOKBOOK_BASE_LIVE_API_PATH
        universe_url += distribution['base_path'] + '/universe'

        universe = client.get(universe_url)

        for content, publication_path in get_content_and_unit_paths(repo):
            u_url = universe[content['name']][content['version']]['download_url']
            self.assertEqual(u_url, urljoin(distribution_base_url, publication_path))

        # Pick a cookbook, and download it from both Fixtures…
        _, unit_path = choice(get_content_and_unit_paths(repo))
        fixtures_hash = hashlib.sha256(
            utils.http_get(urljoin(fixture_u1.url, unit_path))
        ).hexdigest()

        # …and Pulp content
        client.response_handler = api.safe_handler

        unit_url = urljoin(distribution_base_url, unit_path)

        pulp_hash = hashlib.sha256(client.get(unit_url).content).hexdigest()
        self.assertEqual(fixtures_hash, pulp_hash)
