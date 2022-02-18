# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pulpcore.plugin import PulpPluginAppConfig


class PulpCookbookPluginAppConfig(PulpPluginAppConfig):
    """Entry point for pulp_cookbook plugin."""

    name = "pulp_cookbook.app"
    label = "cookbook"
    version = "0.1.0b10.dev"
