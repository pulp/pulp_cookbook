# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from gettext import gettext as _
import os

from django.conf import settings
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import detail_route
from rest_framework import serializers, status
from rest_framework.response import Response

from pulpcore.plugin.models import Artifact
from pulpcore.plugin.serializers import (
    AsyncOperationResponseSerializer,
    RepositorySyncURLSerializer,
)

from pulpcore.plugin.tasking import enqueue_with_reservation

from pulpcore.plugin.viewsets import (
    ContentFilter,
    ContentViewSet,
    BaseDistributionViewSet,
    RemoteViewSet,
    OperationPostponedResponse,
    PublicationViewSet,
    PublisherViewSet,
)

from . import tasks
from .models import (
    CookbookDistribution,
    CookbookPackageContent,
    CookbookRemote,
    CookbookPublication,
    CookbookPublisher,
)
from .serializers import (
    CookbookDistributionSerializer,
    CookbookPackageContentSerializer,
    CookbookRemoteSerializer,
    CookbookPublicationSerializer,
    CookbookPublisherSerializer,
)

from pulp_cookbook.metadata import CookbookMetadata


class CookbookPackageContentFilter(ContentFilter):
    """Filters for the content endpoint."""

    class Meta:
        model = CookbookPackageContent
        fields = ["name", "version", "content_id"]


class CookbookPackageContentViewSet(ContentViewSet):
    """The ViewSet for the content endpoint."""

    endpoint_name = "cookbooks"
    queryset = CookbookPackageContent.objects.all()
    serializer_class = CookbookPackageContentSerializer
    filterset_class = CookbookPackageContentFilter

    @transaction.atomic
    def create(self, request):
        data = request.data
        try:
            artifact = self.get_resource(data["_artifact"], Artifact)
        except KeyError:
            raise serializers.ValidationError(detail={"_artifact": _("This field is required")})

        abs_filepath = os.path.join(settings.MEDIA_ROOT, artifact.file.name)
        try:
            metadata = CookbookMetadata.from_cookbook_file(abs_filepath, data["name"])
        except KeyError:
            raise serializers.ValidationError(detail={"name": _("This field is required")})
        except FileNotFoundError:
            raise serializers.ValidationError(
                detail={"_artifact": _("No metadata.json found in cookbook tar")}
            )

        try:
            if data["version"] != metadata.version:
                raise serializers.ValidationError(
                    detail={"version": _("version does not correspond to version in cookbook tar")}
                )
        except KeyError:
            pass
        data["version"] = metadata.version
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            dependencies=metadata.dependencies,
            content_id_type=CookbookPackageContent.SHA256,
            content_id=artifact.sha256,
        )
        headers = self.get_success_headers(request.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CookbookRemoteViewSet(RemoteViewSet):
    """The ViewSet for the remote endpoint."""

    endpoint_name = "cookbook"
    queryset = CookbookRemote.objects.all()
    serializer_class = CookbookRemoteSerializer

    @swagger_auto_schema(
        operation_description="Trigger an asynchronous task to sync cookbook " "content.",
        responses={202: AsyncOperationResponseSerializer},
    )
    @detail_route(methods=("post",), serializer_class=RepositorySyncURLSerializer)
    def sync(self, request, pk):
        """
        Synchronizes a repository. The ``repository`` field has to be provided.
        """
        remote = self.get_object()
        serializer = RepositorySyncURLSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        repository = serializer.validated_data.get("repository")
        mirror = serializer.validated_data["mirror"]
        result = enqueue_with_reservation(
            tasks.synchronize,
            [repository, remote],
            kwargs={"remote_pk": remote.pk, "repository_pk": repository.pk, "mirror": mirror},
        )
        return OperationPostponedResponse(result, request)


class CookbookPublisherViewSet(PublisherViewSet):
    """The ViewSet for the publisher endpoint."""

    endpoint_name = "cookbook"
    queryset = CookbookPublisher.objects.all()
    serializer_class = CookbookPublisherSerializer


class CookbookPublicationViewSet(PublicationViewSet):
    """
    ViewSet for Cookbook Publications.
    """

    endpoint_name = "cookbook"
    queryset = CookbookPublication.objects.exclude(complete=False)
    serializer_class = CookbookPublicationSerializer

    @swagger_auto_schema(
        operation_description="Trigger an asynchronous task to publish cookbook content.",
        responses={202: AsyncOperationResponseSerializer},
    )
    def create(self, request):
        """
        Publishes a repository.

        Either the ``repository`` or the ``repository_version`` fields can
        be provided but not both at the same time.

        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        repository_version = serializer.validated_data.get("repository_version")
        publisher = serializer.validated_data.get("publisher")

        if publisher:
            publisher_pk = str(publisher.pk)
        else:
            publisher_pk = ""

        result = enqueue_with_reservation(
            tasks.publish,
            [repository_version.repository, publisher_pk],
            kwargs={
                "publisher_pk": publisher_pk,
                "repository_version_pk": str(repository_version.pk),
            },
        )
        return OperationPostponedResponse(result, request)


class CookbookDistributionViewSet(BaseDistributionViewSet):
    """The ViewSet for the distribution endpoint."""

    endpoint_name = "cookbook"
    queryset = CookbookDistribution.objects.all()
    serializer_class = CookbookDistributionSerializer
