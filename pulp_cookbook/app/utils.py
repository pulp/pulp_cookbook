# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf import settings


def pulp_cookbook_content_path():
    """Get base content path from configuration."""
    components = settings.CONTENT_PATH_PREFIX.split("/")
    components[1] = "pulp_cookbook"
    return "/".join(components)
