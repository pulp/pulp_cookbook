# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from gettext import gettext as _

from rest_framework import serializers

from pulpcore.plugin.models import Artifact
from pulpcore.plugin.serializers import (
    ContentSerializer, RelatedField, RemoteSerializer, PublisherSerializer
)

from .models import CookbookPackageContent, CookbookRemote, CookbookPublisher


class CookbookPackageContentSerializer(ContentSerializer):
    name = serializers.CharField(
        help_text=_("name of the cookbook")
    )
    version = serializers.CharField(
        help_text=_("version of the cookbook"),
        required=False
    )
    dependencies = serializers.JSONField(
        help_text=_("dependencies of the cookbook"),
        read_only=True
    )
    artifact = RelatedField(
        view_name='artifacts-detail',
        help_text=_("tar archive containing the cookbook"),
        queryset=Artifact.objects.all()
    )
    artifacts = None

    class Meta:
        fields = tuple(field for field in ContentSerializer.Meta.fields if field != 'artifacts') \
            + ('name', 'version', 'dependencies', 'artifact')
        model = CookbookPackageContent


class CookbookRemoteSerializer(RemoteSerializer):

    cookbooks = serializers.JSONField(
        help_text=_('An optional JSON object in the format {"<cookbook name>":'
                    ' "<version_string>" }. Used to limit the cookbooks to synchronize'
                    ' from the remote'),
        required=False
    )

    class Meta:
        fields = RemoteSerializer.Meta.fields + ('cookbooks', )
        model = CookbookRemote

    # TODO: No support for version specifiers yet, only cookbook names
    def validate_cookbooks(self, value):
        if value == "":  # blank value
            return value
        if isinstance(value, dict):
            if all(value.keys()):
                return value
        raise serializers.ValidationError(
            _('Format must be {"<cookbook_name>" : "version_string" }')
        )


class CookbookPublisherSerializer(PublisherSerializer):
    class Meta:
        fields = PublisherSerializer.Meta.fields
        model = CookbookPublisher
