# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from rest_framework import serializers

from pulpcore.plugin.models import Artifact
from pulpcore.plugin.serializers import ContentSerializer, RemoteSerializer, PublisherSerializer

from .models import CookbookPackageContent, CookbookRemote, CookbookPublisher


class CookbookPackageContentSerializer(ContentSerializer):
    name = serializers.CharField(
        help_text="name of the cookbook"
    )
    version = serializers.CharField(
        help_text="version of the cookbook",
        required=False
    )
    dependencies = serializers.JSONField(
        help_text="dependencies of the cookbook",
        read_only=True
    )
    artifact = serializers.HyperlinkedRelatedField(
        view_name='artifacts-detail',
        help_text="tar archive containing the cookbook",
        queryset=Artifact.objects.all()
    )
    artifacts = None

    class Meta:
        fields = tuple(field for field in ContentSerializer.Meta.fields if field != 'artifacts') \
            + ('name', 'version', 'dependencies', 'artifact')
        model = CookbookPackageContent


class CookbookRemoteSerializer(RemoteSerializer):

    class Meta:
        fields = RemoteSerializer.Meta.fields
        model = CookbookRemote


class CookbookPublisherSerializer(PublisherSerializer):
    class Meta:
        fields = PublisherSerializer.Meta.fields
        model = CookbookPublisher
