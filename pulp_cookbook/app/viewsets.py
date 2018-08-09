# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from gettext import gettext as _

from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import detail_route
from rest_framework import serializers, status
from rest_framework.response import Response

from pulpcore.plugin.models import Artifact
from pulpcore.plugin.serializers import (
    AsyncOperationResponseSerializer,
    RepositoryPublishURLSerializer
)

from pulpcore.plugin.tasking import enqueue_with_reservation

from pulpcore.plugin.viewsets import (
    ContentViewSet,
    OperationPostponedResponse,
    PublisherViewSet,
    BaseFilterSet)

from . import tasks
from .models import CookbookPackageContent, CookbookPublisher
from .serializers import (
    CookbookPackageContentSerializer,
    CookbookPublisherSerializer)

from pulp_cookbook.metadata import CookbookMetadata


class CookbookPackageContentFilter(BaseFilterSet):
    class Meta:
        model = CookbookPackageContent
        fields = [
            'name',
            'version'
        ]


class CookbookPackageContentViewSet(ContentViewSet):
    endpoint_name = 'cookbook/cookbooks'
    queryset = CookbookPackageContent.objects.all()
    serializer_class = CookbookPackageContentSerializer
    filterset_class = CookbookPackageContentFilter

    @transaction.atomic
    def create(self, request):
        data = request.data
        try:
            artifact = self.get_resource(data['artifact'], Artifact)
        except KeyError:
            raise serializers.ValidationError(detail={'artifact': _('This field is required')})

        try:
            metadata = CookbookMetadata.from_cookbook_file(artifact.file.name, data['name'])
        except KeyError:
            raise serializers.ValidationError(detail={'name': _('This field is required')})
        except FileNotFoundError:
            raise serializers.ValidationError(
                detail={'artifact': _('No metadata.json found in cookbook tar')})

        try:
            if data['version'] != metadata.version:
                raise serializers.ValidationError(
                    detail={'version': _('version does not correspond to version in cookbook tar')})
        except KeyError:
            pass
        data['version'] = metadata.version
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        content = serializer.save(dependencies=metadata.dependencies)
        content.artifact = artifact

        headers = self.get_success_headers(request.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CookbookPublisherViewSet(PublisherViewSet):
    endpoint_name = 'cookbook'
    queryset = CookbookPublisher.objects.all()
    serializer_class = CookbookPublisherSerializer

    @swagger_auto_schema(operation_description="Trigger an asynchronous task to publish "
                                               "cookbook content.",
                         responses={202: AsyncOperationResponseSerializer})
    @detail_route(methods=('post',), serializer_class=RepositoryPublishURLSerializer)
    def publish(self, request, pk):
        """
        Publishes a repository. Either the ``repository`` or the ``repository_version`` fields can
        be provided but not both at the same time.
        """
        publisher = self.get_object()
        serializer = RepositoryPublishURLSerializer(data=request.data,
                                                    context={'request': request})
        serializer.is_valid(raise_exception=True)
        repository_version = serializer.validated_data.get('repository_version')

        result = enqueue_with_reservation(
            tasks.publish,
            [repository_version.repository, publisher],
            kwargs={
                'publisher_pk': str(publisher.pk),
                'repository_version_pk': str(repository_version.pk)
            }
        )
        return OperationPostponedResponse(result, request)
