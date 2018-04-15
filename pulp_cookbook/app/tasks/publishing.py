# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import os

from gettext import gettext as _

from celery import shared_task
from django.core.files import File

from pulpcore.plugin.models import (
    RepositoryVersion,
    Publication,
    PublishedArtifact,
    PublishedMetadata)
from pulpcore.plugin.tasking import UserFacingTask, WorkingDirectory

from pulp_cookbook.app.models import CookbookPackageContent, CookbookPublisher
from pulp_cookbook.metadata import Entry, Universe
from pulp_cookbook.app.universe.views import path_template

log = logging.getLogger(__name__)


@shared_task(base=UserFacingTask)
def publish(publisher_pk, repository_version_pk):
    """
    Use provided publisher to create a Publication based on a RepositoryVersion.

    Args:
        publisher_pk (str): Use the publish settings provided by this publisher.
        repository_version_pk (str): Create a publication from this repository version.
    """
    publisher = CookbookPublisher.objects.get(pk=publisher_pk)
    repository_version = RepositoryVersion.objects.get(pk=repository_version_pk)

    log.info(
        _('Publishing: repository=%(repository)s, version=%(version)d, publisher=%(publisher)s'),
        {
            'repository': repository_version.repository.name,
            'version': repository_version.number,
            'publisher': publisher.name,
        })

    with WorkingDirectory():
        with Publication.create(repository_version, publisher) as publication:
            universe = Universe('__universe__')
            universe.write(populate(publication))
            metadata = PublishedMetadata(
                relative_path=os.path.basename(universe.relative_path),
                publication=publication,
                file=File(open(universe.relative_path, 'rb')))
            metadata.save()

    log.info(
        _('Publication: %(publication)s created'),
        {
            'publication': publication.pk
        })


def populate(publication):
    """
    Populate a publication.

    Create published artifacts and yield a Universe Entry for each.

    Args:
        publication (pulpcore.plugin.models.Publication): A Publication to populate.

    Yields:
        Entry: Universe entry for each cookbook
    """
    for content in CookbookPackageContent.objects.filter(
            pk__in=publication.repository_version.content).order_by('-created'):
        relative_path = 'cookbook_files/{}/{}/'.format(content.name,
                                                       content.version.replace('.', '_'))
        for content_artifact in content.contentartifact_set.all():
            art_path = os.path.join(relative_path, content_artifact.relative_path)
            published_artifact = PublishedArtifact(
                relative_path=art_path,
                publication=publication,
                content_artifact=content_artifact)
            published_artifact.save()
            entry = Entry(
                name=content.name,
                version=content.version,
                download_url=path_template(art_path),
                dependencies=content.dependencies)
            yield entry
