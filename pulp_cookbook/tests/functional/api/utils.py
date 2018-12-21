# coding=utf-8
"""Utilities for file plugin tests."""
from pulp_smash import utils
from pulp_smash.pulp3.utils import get_content
from pulp_cookbook.tests.functional.constants import COOKBOOK_CONTENT_NAME


def gen_publisher(**kwargs):
    """Return a semi-random dict for use in creating a publisher."""
    data = {'name': utils.uuid4()}
    data.update(kwargs)
    return data


def get_content_and_unit_paths(repo):
    """Return the publication relative path of content units present in a cookbook repository.

    :param repo: A dict of information about the repository.
    :returns: A list of tuples (content unit, publication path of the unit) present in a given
              repository.
    """
    # The "relative_path" is actually a file path and name
    def rel_path(content):
        path_format = 'cookbook_files/{0}/{2}/{0}-{1}.tar.gz'
        return path_format.format(content['name'],
                                  content['version'],
                                  content['version'].replace('.', '_'))
    content = get_content(repo)
    assert list(content.keys()) == [COOKBOOK_CONTENT_NAME]
    return [(cu, rel_path(cu)) for cu in content[COOKBOOK_CONTENT_NAME]]
