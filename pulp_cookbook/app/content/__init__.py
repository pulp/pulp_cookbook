# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from aiohttp import web

from pulpcore.plugin.content import app

from pulp_cookbook.app.utils import pulp_cookbook_content_path
from .handler import CookbookContentHandler


app.add_routes(
    [
        web.get(
            pulp_cookbook_content_path() + "{path:.+}/universe",
            CookbookContentHandler().handle_universe,
        )
    ]
)
app.add_routes(
    [web.get(pulp_cookbook_content_path() + "{path:.+}", CookbookContentHandler().stream_content)]
)
