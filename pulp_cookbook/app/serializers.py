# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from gettext import gettext as _

from django.conf import settings
from rest_framework import serializers

from pulpcore.plugin import models
from pulpcore.plugin.serializers import (
    PublicationDistributionSerializer,
    PublicationSerializer,
    RelatedField,
    RemoteSerializer,
    SingleArtifactContentUploadSerializer,
)

from pulp_cookbook.app.utils import pulp_cookbook_content_path

from pulp_cookbook.app.models import (
    CookbookDistribution,
    CookbookPackageContent,
    CookbookPublication,
    CookbookRemote,
)

from pulp_cookbook.metadata import CookbookMetadata


class CookbookPackageContentSerializer(SingleArtifactContentUploadSerializer):
    """Serializer for the cookbook content."""

    name = serializers.CharField(help_text=_("name of the cookbook"), required=True)
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
        return data

    def deferred_validate(self, data):
        """Validate that the artifact is a cookbook and extract it's meta-data."""
        data = super().deferred_validate(data)

        try:
            metadata = CookbookMetadata.from_cookbook_file(
                fileobj=data["artifact"].file, name=data["name"]
            )
        except FileNotFoundError:
            raise serializers.ValidationError(
                detail={"artifact": _("No metadata.json found in cookbook tar")}
            )

        try:
            if data["version"] != metadata.version:
                raise serializers.ValidationError(
                    detail={"version": _("version does not correspond to version in cookbook tar")}
                )
        except KeyError:
            pass
        data["version"] = metadata.version
        data["dependencies"] = metadata.dependencies
        data["content_id_type"] = self.Meta.model.SHA256
        data["content_id"] = data["artifact"].sha256
        data["relative_path"] = CookbookPackageContent.relative_path_from_data(data)

        content = self.Meta.model.objects.filter(
            content_id_type=data["content_id_type"],
            content_id=data["content_id"],
            name=data["name"],
            version=data["version"],
        )
        if content.exists():
            raise serializers.ValidationError(
                _(
                    "There is already a cookbook package '{name}-{version}'"
                    " with sha256 '{content_id}'."
                ).format(**data)
            )

        return data

    def update(self, instance, validated_data):
        raise serializers.ValidationError("content is immutable")

    class Meta:
        fields = tuple(
            set(SingleArtifactContentUploadSerializer.Meta.fields) - {"relative_path"}
        ) + ("name", "version", "dependencies", "content_id_type", "content_id")
        model = CookbookPackageContent


class CookbookRemoteSerializer(RemoteSerializer):
    """Serializer for the remote pointing to a universe repo."""

    policy = serializers.ChoiceField(
        help_text=_(
            "The policy to use when downloading content. The possible values include: "
            "'immediate', 'on_demand', and 'streamed'. 'immediate' is the default."
        ),
        choices=models.Remote.POLICY_CHOICES,
        default=models.Remote.IMMEDIATE,
    )

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


class CookbookPublicationSerializer(PublicationSerializer):
    """
    Serializer for Cookbook Publications.
    """

    distributions = RelatedField(
        help_text=_(
            "This publication is currently being served as defined by these distributions."
        ),
        source="cookbook_cookbookdistribution",
        many=True,
        read_only=True,
        view_name="distributions-cookbook/cookbook-detail",
    )

    class Meta:
        fields = PublicationSerializer.Meta.fields + ("distributions",)
        model = CookbookPublication


class CookbookBaseURLField(serializers.CharField):
    """
    Field for the base_url field pointing to the cookbook content app.
    """

    def to_representation(self, value):
        base_path = value
        host = settings.CONTENT_HOST
        prefix = pulp_cookbook_content_path()
        return "/".join((host.strip("/"), prefix.strip("/"), base_path.lstrip("/")))


class CookbookDistributionSerializer(PublicationDistributionSerializer):
    """Serializer for the Distribution."""

    base_url = CookbookBaseURLField(
        source="base_path",
        read_only=True,
        help_text=_("The URL for accessing the universe API as defined by this distribution."),
    )

    class Meta:
        fields = PublicationDistributionSerializer.Meta.fields
        model = CookbookDistribution
