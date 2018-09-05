# coding=utf-8
"""Tests that perform actions over content unit."""
import unittest
from random import choice

from requests.exceptions import HTTPError

from pulp_smash import api, config, utils
from pulp_smash.pulp3.constants import ARTIFACTS_PATH, REPO_PATH
from pulp_smash.pulp3.utils import (
    delete_orphans,
    gen_remote,
    gen_repo,
    get_content,
    sync,
)

from pulp_cookbook.tests.functional.constants import (
    fixture_u1,
    COOKBOOK_CONTENT_PATH,
    COOKBOOK_REMOTE_PATH,
)
from pulp_cookbook.tests.functional.utils import set_up_module as setUpModule  # noqa:F401
from pulp_cookbook.tests.functional.utils import skip_if


class ContentUnitTestCase(unittest.TestCase):
    """CRUD content unit.

    This test targets the following issues:

    * `Pulp #2872 <https://pulp.plan.io/issues/2872>`_
    * `Pulp Smash #870 <https://github.com/PulpQE/pulp-smash/issues/870>`_
    """

    @classmethod
    def setUpClass(cls):
        """Create class-wide variable."""
        cls.cfg = config.get_config()
        delete_orphans(cls.cfg)
        cls.content_unit = {}
        cls.client = api.Client(cls.cfg, api.json_handler)
        download_url = fixture_u1.cookbook_download_url(fixture_u1.example1_name,
                                                        fixture_u1.example1_version)
        cookbooks = {'file': utils.http_get(download_url)}
        cls.artifact = cls.client.post(ARTIFACTS_PATH, files=cookbooks)

    @classmethod
    def tearDownClass(cls):
        """Clean class-wide variable."""
        delete_orphans(cls.cfg)

    def test_01_create_content_unit(self):
        """Create content unit."""
        attrs = _gen_content_unit_attrs(self.artifact, fixture_u1.example1_name)
        self.content_unit.update(self.client.post(COOKBOOK_CONTENT_PATH, attrs))
        for key, val in attrs.items():
            with self.subTest(key=key):
                self.assertEqual(self.content_unit[key], val)

    @skip_if(bool, 'content_unit', False)
    def test_02_read_content_unit(self):
        """Read a content unit by its href."""
        content_unit = self.client.get(self.content_unit['_href'])
        for key, val in self.content_unit.items():
            with self.subTest(key=key):
                self.assertEqual(content_unit[key], val)

    @skip_if(bool, 'content_unit', False)
    def test_02_read_content_units(self):
        """Read a content unit by its name and version."""
        page = self.client.get(COOKBOOK_CONTENT_PATH, params={
            'name': self.content_unit['name'],
            'version': self.content_unit['version'],
        })
        self.assertEqual(len(page['results']), 1)
        for key, val in self.content_unit.items():
            with self.subTest(key=key):
                self.assertEqual(page['results'][0][key], val)

    @skip_if(bool, 'content_unit', False)
    def test_03_partially_update(self):
        """Attempt to update a content unit using HTTP PATCH.

        This HTTP method is not supported and a HTTP exception is expected.
        """
        attrs = _gen_content_unit_attrs(self.artifact, fixture_u1.example1_name)
        with self.assertRaises(HTTPError):
            self.client.patch(self.content_unit['_href'], attrs)

    @skip_if(bool, 'content_unit', False)
    def test_03_fully_update(self):
        """Attempt to update a content unit using HTTP PUT.

        This HTTP method is not supported and a HTTP exception is expected.
        """
        attrs = _gen_content_unit_attrs(self.artifact, fixture_u1.example1_name)
        with self.assertRaises(HTTPError):
            self.client.put(self.content_unit['_href'], attrs)


def _gen_content_unit_attrs(artifact, name):
    """Generate a dict with content unit attributes.

    :param: artifact: A dict of info about the artifact.
    :returns: A dict for use in creating a content unit.
    """
    return {'artifact': artifact['_href'], 'name': name}


class DeleteContentUnitRepoVersionTestCase(unittest.TestCase):
    """Test whether content unit used by a repo version can be deleted.

    This test targets the following issues:

    * `Pulp #3418 <https://pulp.plan.io/issues/3418>`_
    * `Pulp Smash #900 <https://github.com/PulpQE/pulp-smash/issues/900>`_
    """

    def test_all(self):
        """Test whether content unit used by a repo version can be deleted.

        Do the following:

        1. Sync content to a repository.
        2. Attempt to delete a content unit present in a repository version.
           Assert that a HTTP exception was raised.
        3. Assert that number of content units present on the repository
           does not change after the attempt to delete one content unit.
        """
        cfg = config.get_config()
        client = api.Client(cfg, api.json_handler)
        body = gen_remote(fixture_u1.url)
        remote = client.post(COOKBOOK_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote['_href'])
        repo = client.post(REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo['_href'])
        sync(cfg, remote, repo)
        repo = client.get(repo['_href'])
        content = get_content(repo)
        with self.assertRaises(HTTPError):
            client.delete(choice(content)['_href'])
        self.assertEqual(len(content), len(get_content(repo)))
