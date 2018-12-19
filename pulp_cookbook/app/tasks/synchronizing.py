import logging

from gettext import gettext as _
from urllib.parse import urljoin

from pulpcore.plugin.models import Artifact, ProgressBar, Remote, Repository
from pulpcore.plugin.stages import (
    DeclarativeArtifact, DeclarativeContent, DeclarativeVersion, Stage,
    ArtifactDownloader, ArtifactSaver,
    QueryExistingContentUnits, ContentUnitSaver
)

from pulp_cookbook.app.models import CookbookPackageContent, CookbookRemote
from pulp_cookbook.metadata import Universe


log = logging.getLogger(__name__)


class ExistingContentNeedsNoArtifacts(Stage):
    """
    A Stages API stage that removes artifacts that are known (i.e. do not need to be downloaded).

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
                await out_q.put(declarative_content)
        await out_q.put(None)


class CookbookFirstStage(Stage):
    """The first stage of the pulp_cookbook sync pipeline."""

    def __init__(self, remote):
        """
        The first stage of the pulp_cookbook sync pipeline.

        Get the `universe` of the remote repo, parse it and inject a
        DeclarativeContent instance for each cookbook found.

        Args:
            remote (CookbookRemote): The remote data to be used when syncing
        """
        self.remote = remote

    async def __call__(self, in_q, out_q):
        """
        Build and emit `DeclarativeContent` from the Manifest data.

        If a cookbook specifier is set in the remote, cookbooks are filtered
        using this specifier.

        Args: in_q (asyncio.Queue): Unused because the first stage doesn't read
            from an input queue. out_q (asyncio.Queue): The out_q to send
            `DeclarativeContent` objects to

        """
        with ProgressBar(message='Downloading Metadata', total=1) as pb:
            downloader = self.remote.get_downloader(url=urljoin(self.remote.url + '/', 'universe'))
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
                await out_q.put(dc)
        await out_q.put(None)


class CookbookDeclarativeVersion(DeclarativeVersion):
    """Implement pulp_cookbook's stape API pipeline."""

    def pipeline_stages(self, new_version):
        return [
            self.first_stage,
            QueryExistingContentUnits(), ExistingContentNeedsNoArtifacts(),
            ArtifactDownloader(), ArtifactSaver(),
            ContentUnitSaver()
        ]


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
    repository = Repository.objects.get(pk=repository_pk)
    if not remote.url:
        raise ValueError(_('A remote must have a url specified to synchronize.'))

    if remote.policy != Remote.IMMEDIATE:
        raise ValueError(_('Sync supports "{}" policy only').format(Remote.IMMEDIATE))

    first_stage = CookbookFirstStage(remote)
    CookbookDeclarativeVersion(first_stage, repository, mirror).create()
