# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf.urls import url

from .universe.views import UniverseView

urlpatterns = [
    url(r'pulp_cookbook/market/(?P<path>.+)/universe$', UniverseView.as_view())
]
