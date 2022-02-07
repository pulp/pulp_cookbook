# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import os
import tempfile

from gettext import gettext as _

from django.core.files import File

from pulpcore.plugin.models import (
    ProgressReport,
    PublishedArtifact,
    PublishedMetadata,
    RepositoryVersion,
)

from pulp_cookbook.app.models import CookbookPackageContent, CookbookPublication
from pulp_cookbook.metadata import Entry, Universe

log = logging.getLogger(__name__)

BASE_PATH_MARKER = "{{ base_path }}"
BATCH_SIZE = 2000  # Number of objects to query/save


def path_template(artifact_path):
    """Artifact path to write into published '__universe__' file."""
    return BASE_PATH_MARKER + "/" + artifact_path


def replace_all_paths(content, base_url):
    """Replace BASE_PATH_MARKERs with base_url in the give '__universe__' content."""
    return content.replace(BASE_PATH_MARKER, base_url)


def publish(repository_version_pk):
    """
    Create a Publication based on a RepositoryVersion.

    Args:
        repository_version_pk (str): Create a publication from this repository version.

    """
    repository_version = RepositoryVersion.objects.get(pk=repository_version_pk)

    log.info(
        _("Publishing: repository=%(repository)s, version=%(version)d"),
        {"repository": repository_version.repository.name, "version": repository_version.number},
    )

    with tempfile.TemporaryDirectory("."):
        with ProgressReport(
            message="Publishing Content", code="publishing.content"
        ) as progress_report:
            with CookbookPublication.create(repository_version) as publication:
                universe = Universe("__universe__")
                universe.write(populate(publication, progress_report=progress_report))
                PublishedMetadata.create_from_file(
                    relative_path=os.path.basename(universe.relative_path),
                    publication=publication,
                    file=File(open(universe.relative_path, "rb")),
                )

    log.info(_("Publication: %(publication)s created"), {"publication": publication.pk})


def populate(publication, progress_report=None, batch_size=BATCH_SIZE):
    """
    Populate a publication.

    Create published artifacts and yield a Universe Entry for each.

    Args:
        publication (:class:`~pulp_cookbook.models.CookbookPublication`): CookbookPublication
            to populate.
        progress_report (:class:`~pulpcore.plugin.models.ProgressReport`): If given, used to
            report progress
        batch_size (int): Size of content batches to process at once

    Yields:
        Entry: Universe entry for each cookbook

    """
    content_batches = publication.repository_version.content_batch_qs(
        content_qs=CookbookPackageContent.objects.all(),
        batch_size=batch_size,
    )

    for content_slice_qs in content_batches:
        published_artifacts = []
        for content in content_slice_qs.prefetch_related("contentartifact_set"):
            relative_path = "cookbook_files/{}/{}/".format(
                content.name, content.version.replace(".", "_")
            )
            for content_artifact in content.contentartifact_set.all():
                art_path = os.path.join(relative_path, content_artifact.relative_path)
                published_artifacts.append(
                    PublishedArtifact(
                        relative_path=art_path,
                        publication=publication,
                        content_artifact=content_artifact,
                    )
                )
                entry = Entry(
                    name=content.name,
                    version=content.version,
                    download_url=path_template(art_path),
                    dependencies=content.dependencies,
                )
                yield entry
        PublishedArtifact.objects.bulk_create(published_artifacts)
        if progress_report:
            progress_report.increase_by(len(published_artifacts))
