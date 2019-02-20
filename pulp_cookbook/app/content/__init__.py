# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from aiohttp import web

from .handler import CookbookContentHandler, pulp_cookbook_content_path

from pulpcore.plugin.content import app


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
