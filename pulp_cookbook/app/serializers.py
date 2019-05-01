# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from gettext import gettext as _

from rest_framework import serializers

from pulpcore.plugin.serializers import (
    DetailRelatedField,
    PublicationSerializer,
    PublisherSerializer,
    RemoteSerializer,
    SingleArtifactContentSerializer,
)

from .models import CookbookPackageContent, CookbookPublication, CookbookPublisher, CookbookRemote


class CookbookPackageContentSerializer(SingleArtifactContentSerializer):
    """Serializer for the cookbook content."""

    name = serializers.CharField(help_text=_("name of the cookbook"))
    version = serializers.CharField(help_text=_("version of the cookbook"), required=False)
    dependencies = serializers.JSONField(
        help_text=_("dependencies of the cookbook"), read_only=True
    )
    content_id_type = serializers.HiddenField(default=CookbookPackageContent.SHA256)
    content_id = serializers.CharField(
        help_text=_(
            "content_id of the cookbook (UUID (lazy download)/SHA256 (immediate download/import)"
        ),
        read_only=True,
    )

    def validate(self, data):
        """Validate the CookbookPackageContent data."""
        data = super().validate(data)
        data["_relative_path"] = CookbookPackageContent.relative_path_from_data(data)
        return data

    def update(self, instance, validated_data):
        raise serializers.ValidationError("content is immutable")

    class Meta:
        fields = tuple(set(SingleArtifactContentSerializer.Meta.fields) - {"_relative_path"}) + (
            "name",
            "version",
            "dependencies",
            "content_id_type",
            "content_id",
        )
        model = CookbookPackageContent


class CookbookRemoteSerializer(RemoteSerializer):
    """Serializer for the remote pointing to a universe repo."""

    cookbooks = serializers.JSONField(
        help_text=_(
            'An optional JSON object in the format {"<cookbook name>":'
            ' "<version_string>" }. Used to limit the cookbooks to synchronize'
            " from the remote"
        ),
        required=False,
    )

    class Meta:
        fields = RemoteSerializer.Meta.fields + ("cookbooks",)
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
    """Serializer for the publisher."""

    class Meta:
        fields = PublisherSerializer.Meta.fields
        model = CookbookPublisher


class CookbookPublicationSerializer(PublicationSerializer):
    """
    Serializer for Cookbook Publications.
    """

    publisher = DetailRelatedField(
        help_text=_("The publisher that created this publication."),
        queryset=CookbookPublisher.objects.all(),
        required=False,
    )

    class Meta:
        fields = PublicationSerializer.Meta.fields + ("publisher",)
        model = CookbookPublication
