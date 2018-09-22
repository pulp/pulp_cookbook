# coding=utf-8

from typing import Dict, Iterable, List, Optional
from urllib.parse import urljoin

from pulp_smash.pulp3.constants import (
    BASE_PUBLISHER_PATH,
    BASE_REMOTE_PATH,
    CONTENT_PATH
)

FIXTURES_BASE_URL = 'https://pulpcookbook.s3.wasabisys.com/'

COOKBOOK_CONTENT_PATH = urljoin(CONTENT_PATH, 'cookbook/cookbooks/')

COOKBOOK_REMOTE_PATH = urljoin(BASE_REMOTE_PATH, 'cookbook/')

COOKBOOK_PUBLISHER_PATH = urljoin(BASE_PUBLISHER_PATH, 'cookbook/')

COOKBOOK_BASE_LIVE_API_PATH = '/pulp_cookbook/market/'


class CookbookFixture:
    """Class holding information about a universe cookbook repo fixture."""

    def __init__(self, repo_name: str, cookbooks: Dict[str, List[str]]) -> None:
        self.url = urljoin(FIXTURES_BASE_URL, repo_name + '/')
        self.cookbooks = cookbooks

    def cookbook_count(self, names: Optional[Iterable] = None) -> int:
        """Return the number of cookbooks or the number of cookbooks with a specific name."""
        if not names:
            names = self.cookbooks.keys()
        return sum(len(self.cookbooks[name]) for name in names)

    def cookbook_download_url(self, name: str, version: str):
        uversion = version.replace('.', '_')
        print("kjk", self.url)
        return urljoin(self.url, f"cookbook_files/{name}/{uversion}/{name}-{version}.tar.gz")


fixture_u1 = CookbookFixture('u1', {
    "apache2": ["5.0.1", "5.0.0", "3.0.1", "1.10.2", "1.9.6", "1.9.1"],
    "apt": ["7.0.0", "6.0.1", "5.0.1"],
    "ubuntu": ["2.0.1", "1.0.0"],
    "nginx": ["8.0.0", "2.7.4", "2.7.2", "2.7.0", "2.6.0", "2.5.0"]
})
fixture_u1.example1_name = 'ubuntu'
fixture_u1.example1_version = '2.0.1'
fixture_u1.example2_name = 'nginx'
fixture_u1.example2_version = '2.7.4'

COOKBOOK2_FIXTURE_URL = urljoin(FIXTURES_BASE_URL, 'u2/')
"""The URL to a cookbook universe repository."""

COOKBOOK2_URL = urljoin(COOKBOOK2_FIXTURE_URL, '1.iso')
"""The URL to an ISO cookbook at :data:`COOKBOOK2_FIXTURE_URL`."""
