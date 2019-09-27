# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action

from pulpcore.plugin.serializers import (
    AsyncOperationResponseSerializer,
    RepositorySyncURLSerializer,
)

from pulpcore.plugin.tasking import enqueue_with_reservation

from pulpcore.plugin.viewsets import (
    BaseDistributionViewSet,
    ContentFilter,
    OperationPostponedResponse,
    PublicationViewSet,
    RemoteViewSet,
    SingleArtifactContentUploadViewSet,
)

from . import tasks
from .models import (
    CookbookDistribution,
    CookbookPackageContent,
    CookbookRemote,
    CookbookPublication,
)
from .serializers import (
    CookbookDistributionSerializer,
    CookbookPackageContentSerializer,
    CookbookRemoteSerializer,
    CookbookPublicationSerializer,
)


class CookbookPackageContentFilter(ContentFilter):
    """Filters for the content endpoint."""

    class Meta:
        model = CookbookPackageContent
        fields = ["name", "version", "content_id"]


class CookbookPackageContentViewSet(SingleArtifactContentUploadViewSet):
    """The ViewSet for the content endpoint."""

    endpoint_name = "cookbooks"
    queryset = CookbookPackageContent.objects.order_by("_id").prefetch_related("_artifacts")
    serializer_class = CookbookPackageContentSerializer
    filterset_class = CookbookPackageContentFilter


class CookbookRemoteViewSet(RemoteViewSet):
    """The ViewSet for the remote endpoint."""

    endpoint_name = "cookbook"
    queryset = CookbookRemote.objects.all()
    serializer_class = CookbookRemoteSerializer

    @swagger_auto_schema(
        operation_description="Trigger an asynchronous task to sync cookbook " "content.",
        responses={202: AsyncOperationResponseSerializer},
    )
    @action(detail=True, methods=["post"], serializer_class=RepositorySyncURLSerializer)
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

        result = enqueue_with_reservation(
            tasks.publish,
            [repository_version.repository],
            kwargs={"repository_version_pk": str(repository_version.pk)},
        )
        return OperationPostponedResponse(result, request)


class CookbookDistributionViewSet(BaseDistributionViewSet):
    """The ViewSet for the distribution endpoint."""

    endpoint_name = "cookbook"
    queryset = CookbookDistribution.objects.all()
    serializer_class = CookbookDistributionSerializer
