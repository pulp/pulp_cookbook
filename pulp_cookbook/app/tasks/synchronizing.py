import asyncio
import logging

from gettext import gettext as _
from urllib.parse import urljoin

from pulpcore.plugin.models import Artifact, ProgressBar, Repository, RepositoryVersion
from pulpcore.plugin.stages import (
    DeclarativeArtifact, DeclarativeContent, DeclarativeVersion, Stage,
    ArtifactDownloader, ArtifactSaver,
    QueryExistingContentUnits, ContentUnitSaver, ContentUnitAssociation, ContentUnitUnassociation,
    EndStage, create_pipeline
)
from pulpcore.plugin.tasking import WorkingDirectory

from pulp_cookbook.app.models import CookbookPackageContent, CookbookRemote
from pulp_cookbook.metadata import Universe


log = logging.getLogger(__name__)


class StageBase(Stage):

    @staticmethod
    async def batches(in_q):
        """
        Asynchronous iterator yielding batches of :class:`DeclarativeContent` from `in_q`.

        Args:
            in_q (:class:`asyncio.Queue`): The queue to receive
                :class:`~pulpcore.plugin.stages.DeclarativeContent` objects from.

        Yields:
            A list of :class:`DeclarativeContent` instances

        Examples:
            Used in stages to get large chunks of declarative_content instances from the
            `in_q`::

                async for batch in self.batches(in_q):
                    # process the batch and queue the result to out_q
                await out_q.put(None) # stage is finished
        """
        batch = []
        shutdown = False

        def add_to_batch(batch, content):
            if content is None:
                return True
            batch.append(content)
            return False

        while not shutdown:
            content = await in_q.get()
            shutdown = add_to_batch(batch, content)
            while not shutdown:
                try:
                    content = in_q.get_nowait()
                except asyncio.QueueEmpty:
                    break
                else:
                    shutdown = add_to_batch(batch, content)
            if batch:
                yield batch
            batch = []

    @staticmethod
    async def greedy_put(out_q, declarative_content):
        """queue.put() that only reschedules when queue is full"""
        try:
            out_q.put_nowait(declarative_content)
        except asyncio.QueueFull:
            await out_q.put(declarative_content)


class ExistingContentNeedsNoArtifacts(StageBase):
    """
    A Stages API stage that removes all
    :class:`~pulpcore.plugin.stages.DeclarativeArtifact` instances from
    :class:`~pulpcore.plugin.stages.DeclarativeContent` units if the respective
    :class:`~pulpcore.plugin.models.Content` is already existing.
    """

    async def __call__(self, in_q, out_q):
        """
        The coroutine for this stage.

        Args:
            in_q (:class:`asyncio.Queue`): The queue to receive
                :class:`~pulpcore.plugin.stages.DeclarativeContent` objects from.
            out_q (:class:`asyncio.Queue`): The queue to put
                :class:`~pulpcore.plugin.stages.DeclarativeContent` into.

        Returns:
            The coroutine for this stage.
        """
        async for batch in self.batches(in_q):
            for declarative_content in batch:
                if declarative_content.content.pk is not None:
                    declarative_content.d_artifacts = []
                await self.greedy_put(out_q, declarative_content)
        await out_q.put(None)


class CookbookFirstStage(StageBase):

    def __init__(self, remote):
        """
        The first stage of the pulp_cookbook sync pipeline.

        Args:
            remote (CookbookRemote): The remote data to be used when syncing
        """
        self.remote = remote

    async def __call__(self, in_q, out_q):
        """
        Build and emit `DeclarativeContent` from the Manifest data. If a
        cookbook specifier is set in the remote, cookbooks are filtered using
        this specifier.

        Args:
            in_q (asyncio.Queue): Unused because the first stage doesn't read from an input queue.
            out_q (asyncio.Queue): The out_q to send `DeclarativeContent` objects to
        """
        with ProgressBar(message='Downloading Metadata', total=1) as pb:
            downloader = self.remote.get_downloader(urljoin(self.remote.url + '/', 'universe'))
            result = await downloader.run()
            pb.increment()

        cookbook_names = self.remote.specifier_cookbook_names()

        with ProgressBar(message='Parsing Metadata') as pb:
            universe = Universe(result.path)
            for entry in universe.read():
                if cookbook_names and entry.name not in cookbook_names:
                    continue
                cookbook = CookbookPackageContent(name=entry.name, version=entry.version,
                                                  dependencies=entry.dependencies)
                artifact = Artifact()
                da = DeclarativeArtifact(artifact, entry.download_url,
                                         cookbook.relative_path(), self.remote)
                dc = DeclarativeContent(content=cookbook, d_artifacts=[da])
                pb.increment()
                await self.greedy_put(out_q, dc)
        await out_q.put(None)


class CookbookDeclarativeVersion(DeclarativeVersion):

    def create(self):
        """
        Perform the work. This is the long-blocking call where all syncing occurs.
        """
        with WorkingDirectory():
            with RepositoryVersion.create(self.repository) as new_version:
                loop = asyncio.get_event_loop()
                stages = [
                    self.first_stage,
                    QueryExistingContentUnits(), ExistingContentNeedsNoArtifacts(),
                    ArtifactDownloader(), ArtifactSaver(),
                    ContentUnitSaver(),
                    ContentUnitAssociation(new_version)
                ]
                if self.mirror:
                    stages.extend([ContentUnitUnassociation(new_version), EndStage()])
                else:
                    stages.append(EndStage())
                pipeline = create_pipeline(stages)
                loop.run_until_complete(pipeline)


def synchronize(remote_pk, repository_pk, mirror):
    """
    Create a new version of the repository that is synchronized with the remote
    as specified by the remote.

    Args:
        remote_pk (str): The remote PK.
        repository_pk (str): The repository PK.
        mirror (bool): True for mirror mode, False for additive.

    Raises:
        ValueError: When url is empty.
    """
    remote = CookbookRemote.objects.get(pk=remote_pk)
    repository = Repository.objects.get(pk=repository_pk)

    if not remote.url:
        raise ValueError(_('A remote must have a url specified to synchronize.'))

    first_stage = CookbookFirstStage(remote)
    CookbookDeclarativeVersion(first_stage, repository, mirror).create()
