"""Utilities for cookbook plugin tests."""
import functools

from pulp_smash import utils
from pulp_smash.pulp3.utils import get_added_content, get_content, get_removed_content

from pulp_cookbook.tests.functional.constants import COOKBOOK_CONTENT_NAME


def gen_publisher(**kwargs):
    """Return a semi-random dict for use in creating a publisher."""
    data = {'name': utils.uuid4()}
    data.update(kwargs)
    return data


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
        path_format = 'cookbook_files/{0}/{2}/{0}-{1}.tar.gz'
        return path_format.format(content['name'],
                                  content['version'],
                                  content['version'].replace('.', '_'))
    return [(cu, rel_path(cu)) for cu in get_cookbook_content(repo)]
