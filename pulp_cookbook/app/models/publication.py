# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later


from pulpcore.plugin.models import PublicationDistribution, Publication


class CookbookPublication(Publication):
    """
    Publication for 'cookbook' content.
    """

    TYPE = "cookbook"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class CookbookDistribution(PublicationDistribution):
    """
    Distribution for 'cookbook' content.
    """

    TYPE = "cookbook"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
