# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import aiohttp
import logging

from django.conf import settings
from django.db import IntegrityError, transaction

from pulpcore.plugin.content import Handler, PathNotResolved

from pulp_cookbook.app.tasks.publishing import replace_all_paths
from pulp_cookbook.app.utils import pulp_cookbook_content_path

log = logging.getLogger(__name__)


class CookbookContentHandler(Handler):
    """
    Serve cookbook repositories using the universe API.

    This content handler is pretty standard with two exceptions:
    1. Serve the `/universe` endpoint using dynamic replacement for the URLs
    2. When saving ContentArtifact, try to 'update' the CookbookPackageContent
       with the digest of the downloaded artifact.
    """

    async def handle_universe(self, request):
        """
        Serve the '__universe__' metadata object at '/universe'.

        Since the '/universe' endpoint contains absolute URLs, translate
        the content of '__universe__' on the fly.
        """
        path = request.match_info["path"] + "/universe"
        distribution = Handler._match_distribution(path).cast()
        Handler._permit(request, distribution)
        publication = distribution.publication
        if not publication:
            raise PathNotResolved(path)
        pm = publication.published_metadata.get(relative_path="__universe__")
        try:
            with pm.file.open("rb") as u:
                content = u.read().decode("utf-8")
        except FileNotFoundError:
            return PathNotResolved(path)
        except PermissionError:
            return aiohttp.web_exceptions.HTTPForbidden
        content = replace_all_paths(
            content, self._get_content_base_url(request) + distribution.base_path
        )
        return aiohttp.web.Response(body=content, content_type="application/json", charset="utf-8")

    def _save_artifact(self, download_result, remote_artifact):
        new_artifact = super()._save_artifact(
            download_result=download_result, remote_artifact=remote_artifact
        )
        content_artifact = remote_artifact.content_artifact
        content = content_artifact.content.cast()
        try:
            # Try to 'upgrade' the content unit as the digest is known now. This
            # might fail if another identical content unit exists already.
            # We can just ignore this case: As the artifact will be created nevertheless,
            # this method won't be called again for the content_artifact.
            with transaction.atomic():
                content.set_sha256_digest(new_artifact.sha256)
                content.save()
        except IntegrityError:
            pass
        return new_artifact

    def _get_content_base_url(self, request):
        if settings.CONTENT_HOST:
            host = settings.CONTENT_HOST
        else:
            host = request.host
        host = "{}://{}".format(request.scheme, host)

        return host + pulp_cookbook_content_path()
