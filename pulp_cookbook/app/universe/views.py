# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound

from rest_framework import views, reverse

from pulpcore.app.models import Distribution

BASE_PATH_MARKER = '{{ base_path }}'


def path_template(artifact_path):
    return BASE_PATH_MARKER + '/' + artifact_path


def replace_all_paths(content, base_url):
    return content.replace(BASE_PATH_MARKER, base_url)


class UniverseView(views.APIView):
    """
    Provides the GET ../universe endpoint.

    Publishing prepares a "__universe__" matadata artifact with placeholders for
    the actual content base URL (which is known only after distribution)

    Use this artifact and the actual base URL to create the universe content.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request, path):
        distro = get_object_or_404(Distribution, base_path=self.kwargs['path'])
        universe_md = distro.publication.published_metadata.get(relative_path='__universe__')
        try:
            with universe_md.file.open('rb') as u:
                content = u.read().decode('utf-8')
        except FileNotFoundError:
            return HttpResponseNotFound()
        except PermissionError:
            return HttpResponseForbidden()
        content = replace_all_paths(content,
                                    self._get_content_base_url(request) + distro.base_path)
        return HttpResponse(content, content_type='application/json; charset=utf-8')

    def _get_content_base_url(self, request):
        if settings.CONTENT['host']:
            host = settings.CONTENT['host']
        else:
            host = request.get_host()
        host = "{}://{}".format(request.scheme, host)

        return host + reverse.reverse('content-app')
