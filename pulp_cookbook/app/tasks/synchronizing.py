# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import logging

from collections import defaultdict
from gettext import gettext as _
from urllib.parse import urljoin

from django.db.models import Prefetch, Q

from pulpcore.plugin.models import Artifact, ContentArtifact, ProgressReport, Remote
from pulpcore.plugin.stages import (
    DeclarativeArtifact,
    DeclarativeContent,
    DeclarativeVersion,
    Stage,
    ArtifactDownloader,
    ArtifactSaver,
    QueryExistingContents,
    RemoteArtifactSaver,
    ContentSaver,
)

from pulp_cookbook.app.models import CookbookPackageContent, CookbookRemote, CookbookRepository
from pulp_cookbook.metadata import Universe

log = logging.getLogger(__name__)


class UpdateContentWithDownloadResult(Stage):
    """
    A stage that sets the content_id (SHA256 from the artifact).

    Set the content_id to the SHA256 checksum for "unsaved" content or, if
    saved content has no/a different checksum, create a new content instance
    with a SHA256 content_id.
    """

    async def run(self):
        async for d_content in self.items():
            download_sha256 = d_content.d_artifacts[0].artifact.sha256
            if d_content.content._state.adding:
                d_content.content.set_sha256_digest(download_sha256)
            else:
                if d_content.content.content_id != download_sha256:
                    # To keep previous repository versions untouched, create a
                    # new content unit instead of modifying the existing
                    # content.
                    # To copy multiple inheritance models, we need to set both
                    # pk and pulp_id to None and, as stages look at _state.adding,
                    # reset that as well...
                    d_content.content.pk = None
                    d_content.content.pulp_id = None
                    d_content.content._state.adding = True
                    d_content.content.set_sha256_digest(download_sha256)
            await self.put(d_content)


class QueryExistingRepoContentAndArtifacts(Stage):
    """
    A Stages API stage that searches for saved Content and Artifacts in the base repo version.

    This stage expects :class:`~pulpcore.plugin.stages.DeclarativeContent` units
    from `in_q` and inspects their associated
    :class:`~pulpcore.plugin.models.Content` instance.

    This stage inspects any "unsaved" Content unit objects and searches for
    existing saved Content units with the same key. The search is constrained to
    the content of the given repository version `new_version` and use the query
    :class:`~pulpcore.plugin.models.Content.repo_q()` and the key
    :class:`~pulpcore.plugin.models.Content.repo_key_fields`.

    Any existing Content objects found replace their "unsaved" counterpart in
    the :class:`~pulpcore.plugin.stages.DeclarativeContent` object.
    Additionally, inspect the associated
    :class:`~pulpcore.plugin.stages.DeclarativeArtifact` units:  Any existing
    Artifact objects found replace their "unsaved" counterpart in the
    :class:`~pulpcore.plugin.stages.DeclarativeArtifact` object (the match is
    done on `relative_path`).

    Each :class:`~pulpcore.plugin.stages.DeclarativeContent` is sent to `out_q`
    after it has been handled.

    This stage drains all available items from `in_q` and batches everything
    into one large call to the db for efficiency.

    Args: new_version (:class:`~pulpcore.plugin.models.RepositoryVersion`):
        Optional repository version to search content in.

    """

    def __init__(self, new_version, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_version = new_version

    async def run(self):
        async for batch in self.batches():
            self._process_batch(batch)
            for declarative_content in batch:
                await self.put(declarative_content)

    def _process_batch(self, batch):
        unsaved_d_cs = [dc for dc in batch if dc.content._state.adding]

        content_q_by_type = defaultdict(lambda: Q(pk=None))
        # declarative_content by model type and repo key
        d_c_by_mt_rk = defaultdict(dict)

        for declarative_content in unsaved_d_cs:
            m_type = type(declarative_content.content)
            unit_q = declarative_content.content.repo_q()
            content_q_by_type[m_type] = content_q_by_type[m_type] | unit_q
            d_c_by_mt_rk[m_type][declarative_content.content.repo_key_value()] = declarative_content

        for model_type in content_q_by_type:
            self._associate_model_type(
                model_type, content_q_by_type[model_type], d_c_by_mt_rk[model_type]
            )

    def _associate_model_type(self, model_type, q, d_c_by_repo_key):
        content_filter = model_type.objects.filter(pk__in=self.new_version.content)
        content_filter = content_filter.filter(q)
        # prefetch the related ContentArtifact and Artifact objects:
        content_filter = content_filter.prefetch_related(
            Prefetch(
                "_artifacts",
                queryset=(
                    ContentArtifact.objects.filter(artifact__isnull=False).select_related(
                        "artifact"
                    )
                ),
                to_attr="c_as_with_artifact",
            )
        )
        for content in content_filter:
            repo_key = content.repo_key_value()
            try:
                declarative_content = d_c_by_repo_key[repo_key]
            except KeyError:
                pass
            else:
                declarative_content.content = content
                for c_a in content.c_as_with_artifact:
                    for d_a in declarative_content.d_artifacts:
                        if d_a.relative_path == c_a.relative_path:
                            d_a.artifact = c_a.artifact
                del content.c_as_with_artifact


class CookbookFirstStage(Stage):
    """The first stage of the pulp_cookbook sync pipeline."""

    def __init__(self, remote, download_artifacts, *args, **kwargs):
        """
        The first stage of the pulp_cookbook sync pipeline.

        Get the `universe` of the remote repo, parse it and inject a
        DeclarativeContent instance for each cookbook found.

        Args:
            remote (CookbookRemote): The remote data to be used when syncing

        """
        super().__init__(*args, **kwargs)
        self.remote = remote
        self.download_artifacts = download_artifacts

    async def run(self):
        """
        Build and emit `DeclarativeContent` from the Manifest data.

        If a cookbook specifier is set in the remote, cookbooks are filtered
        using this specifier.

        """
        with ProgressReport(
            message="Downloading Metadata", code="downloading.metadata", total=1
        ) as pb:
            downloader = self.remote.get_downloader(url=urljoin(self.remote.url + "/", "universe"))
            result = await downloader.run()
            pb.increment()

        cookbook_names = self.remote.specifier_cookbook_names()

        with ProgressReport(message="Parsing Metadata", code="parsing.metadata") as pb:
            universe = Universe(result.path)
            for entry in universe.read():
                if cookbook_names and entry.name not in cookbook_names:
                    continue
                cookbook = CookbookPackageContent(
                    name=entry.name, version=entry.version, dependencies=entry.dependencies
                )
                artifact = Artifact()
                da = DeclarativeArtifact(
                    artifact=artifact,
                    url=entry.download_url,
                    relative_path=cookbook.relative_path(),
                    remote=self.remote,
                    deferred_download=not self.download_artifacts,
                )
                dc = DeclarativeContent(content=cookbook, d_artifacts=[da])
                pb.increment()
                await self.put(dc)


class CookbookDeclarativeVersion(DeclarativeVersion):
    """Implement pulp_cookbook's stage API pipeline."""

    def __init__(self, download_artifacts, *args, **kwargs):
        self.download_artifacts = download_artifacts
        super().__init__(*args, **kwargs)

    def pipeline_stages(self, new_version):
        pipeline = [self.first_stage, QueryExistingRepoContentAndArtifacts(new_version=new_version)]
        if self.download_artifacts:
            pipeline.extend(
                [
                    ArtifactDownloader(),
                    ArtifactSaver(),
                    UpdateContentWithDownloadResult(),
                    QueryExistingContents(),  # share content with known digest
                ]
            )
        pipeline.append(ContentSaver())
        pipeline.append(RemoteArtifactSaver())
        return pipeline


def synchronize(remote_pk, repository_pk, mirror):
    """
    Create a new version of the repository that is synchronized with the remote.

    Args:
        remote_pk (str): The remote PK.
        repository_pk (str): The repository PK.
        mirror (bool): True for mirror mode, False for additive.

    Raises:
        ValueError: When url is empty.

    """
    remote = CookbookRemote.objects.get(pk=remote_pk)
    repository = CookbookRepository.objects.get(pk=repository_pk)
    if not remote.url:
        raise ValueError(_("A remote must have a url specified to synchronize."))

    download = remote.policy == Remote.IMMEDIATE  # Interpret policy to download Artifacts or not

    first_stage = CookbookFirstStage(remote=remote, download_artifacts=download)
    dv = CookbookDeclarativeVersion(
        first_stage=first_stage, repository=repository, mirror=mirror, download_artifacts=download
    )
    dv.create()
