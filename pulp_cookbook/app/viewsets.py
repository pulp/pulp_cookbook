# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from pulpcore.plugin.actions import ModifyRepositoryActionMixin

from pulpcore.plugin.serializers import (
    AsyncOperationResponseSerializer,
    RepositorySyncURLSerializer,
)

from pulpcore.plugin.tasking import dispatch

from pulpcore.plugin.viewsets import (
    DistributionViewSet,
    ContentFilter,
    OperationPostponedResponse,
    PublicationViewSet,
    RemoteViewSet,
    RepositoryViewSet,
    RepositoryVersionViewSet,
    SingleArtifactContentUploadViewSet,
)

from . import tasks
from .models import (
    CookbookDistribution,
    CookbookPackageContent,
    CookbookRemote,
    CookbookRepository,
    CookbookPublication,
)
from .serializers import (
    CookbookDistributionSerializer,
    CookbookPackageContentSerializer,
    CookbookRemoteSerializer,
    CookbookRepositorySerializer,
    CookbookPublicationSerializer,
)


class CookbookPackageContentFilter(ContentFilter):
    """Filters for the content endpoint."""

    class Meta:
        model = CookbookPackageContent
        fields = ["name", "version", "content_id"]


class CookbookPackageContentViewSet(SingleArtifactContentUploadViewSet):
    """Cookbook Content Endpoint.

    <!-- User-facing documentation, rendered as html-->
    CookbookContent represents a single cookbook, which can be added and removed
    from repositories.
    """

    endpoint_name = "cookbooks"
    queryset = CookbookPackageContent.objects.order_by("pulp_id").prefetch_related("_artifacts")
    serializer_class = CookbookPackageContentSerializer
    filterset_class = CookbookPackageContentFilter


class CookbookRepositoryViewSet(ModifyRepositoryActionMixin, RepositoryViewSet):
    """
    Cookbook Repository Endpoint.

    <!-- User-facing documentation, rendered as html-->
    CookbookRepository represents a single cookbook repository, to which content can
    be synced, added, or removed.
    """

    endpoint_name = "cookbook"
    queryset = CookbookRepository.objects.all()
    serializer_class = CookbookRepositorySerializer

    @extend_schema(
        description="Trigger an asynchronous task to sync cookbook content.",
        responses={202: AsyncOperationResponseSerializer},
    )
    @action(detail=True, methods=["post"], serializer_class=RepositorySyncURLSerializer)
    def sync(self, request, pk):
        """
        Synchronizes a Cookbook repository.

        The ``repository`` field has to be provided.
        """
        serializer = RepositorySyncURLSerializer(
            data=request.data, context={"request": request, "repository_pk": pk}
        )
        serializer.is_valid(raise_exception=True)

        repository = self.get_object()
        remote = serializer.validated_data.get("remote", repository.remote)

        mirror = serializer.validated_data.get("mirror", False)
        result = dispatch(
            tasks.synchronize,
            exclusive_resources=[repository, remote],
            kwargs={"remote_pk": remote.pk, "repository_pk": repository.pk, "mirror": mirror},
        )
        return OperationPostponedResponse(result, request)


class CookbookRepositoryVersionViewSet(RepositoryVersionViewSet):
    """Cookbook Repository Version Endpoint.

    <!-- User-facing documentation, rendered as html-->
    CookbookRepositoryVersion represents a single cookbook repository version.
    """

    parent_viewset = CookbookRepositoryViewSet


class CookbookRemoteViewSet(RemoteViewSet):
    """Cookbook Remote Endpoint.

    <!-- User-facing documentation, rendered as html-->
    CookbookRemote represents an external source of <a
    href="#tag/content:-cookbooks">Cookbook Content</a>.  The target url of a
    CookbookRemote must point to a <a
    href="https://docs.chef.io/supermarket_api.html">universe API</a> endpont.
    """

    endpoint_name = "cookbook"
    queryset = CookbookRemote.objects.all()
    serializer_class = CookbookRemoteSerializer


class CookbookPublicationViewSet(PublicationViewSet):
    """File Publication Endpoint.

    <!-- User-facing documentation, rendered as html-->
    A CookbookPublication contains metadata about all the <a
    href="#tag/content:-cookbooks">Cookbook Content</a> in a particular <a
    href="#tag/repositories:-cookbook-versions">Cookbook Repository Version.</a>
    Once a CookbookPublication has been created, it can be hosted using the <a
    href="#tag/distributions:-cookbook">Cookbook Distribution API.</a>
    """

    endpoint_name = "cookbook"
    queryset = CookbookPublication.objects.exclude(complete=False)
    serializer_class = CookbookPublicationSerializer

    @extend_schema(
        description="Trigger an asynchronous task to publish cookbook content.",
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

        result = dispatch(
            tasks.publish,
            exclusive_resources=[repository_version.repository],
            kwargs={"repository_version_pk": str(repository_version.pk)},
        )
        return OperationPostponedResponse(result, request)


class CookbookDistributionViewSet(DistributionViewSet):
    """Cookbook Distreibution Endpoint.

    <!-- User-facing documentation, rendered as html-->
    CookbookDistributions host <a href="#tag/publications:-cookbook">Cookbook
    Publications</a> which makes the metadata and the referenced <a
    href="#tag/content:-cookbooks">Cookbook Content</a> available to clients
    like berkshelf. Additionally, a CookbookDistribution with an associated
    CookbookPublication can be the target url of a <a
    href="#tag/remotes:-cookbook">Cookbook Remote</a> , allowing another
    instance of Pulp to sync the content.
    """

    endpoint_name = "cookbook"
    queryset = CookbookDistribution.objects.all()
    serializer_class = CookbookDistributionSerializer
