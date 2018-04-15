# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pulpcore.plugin import PulpPluginAppConfig


class PulpCookbookPluginAppConfig(PulpPluginAppConfig):
    name = 'pulp_cookbook.app'
    label = 'pulp_cookbook'
