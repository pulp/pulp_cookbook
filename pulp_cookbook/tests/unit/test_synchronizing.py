from unittest.mock import Mock

from django.test import TestCase

from pulpcore.plugin.models import Artifact
from pulpcore.plugin.stages import DeclarativeArtifact, DeclarativeContent

from pulp_cookbook.app.models import CookbookPackageContent, CookbookRemote
from pulp_cookbook.app.tasks.synchronizing import (
    QueryExistingContentUnits,
    QueryExistingRepoContentAndArtifacts
)


class QueryExistingContentUnitsTestCase(TestCase):
    """Verify QueryExistingContentUnits stage for both natural and repo keys."""

    def setUp(self):
        self.c1 = CookbookPackageContent.objects.create(name='c1', version='1.0.0',
                                                        content_id='1', dependencies={})

    def new_version_all_content(self):
        """Provide a mock for a repository version containing all content."""
        new_version = Mock()
        new_version.content = CookbookPackageContent.objects.all()
        return new_version

    def test_content_associated_using_repo_key(self):
        dc_c1 = CookbookPackageContent(name='c1', version='1.0.0',
                                       dependencies={})
        dc_c2 = CookbookPackageContent(name='c2', version='1.0.0',
                                       dependencies={})

        batch = [
            DeclarativeContent(content=dc_c1, d_artifacts=[]),
            DeclarativeContent(content=dc_c2, d_artifacts=[]),
        ]
        stage = QueryExistingContentUnits(new_version=self.new_version_all_content())
        stage._process_batch(batch)
        self.assertEqual(batch[0].content.content_id, '1')
        self.assertEqual(batch[0].content.pk, self.c1.pk)
        self.assertIsNone(batch[1].content.pk)

    def test_content_associated_using_natural_key(self):
        dc_c1 = CookbookPackageContent(name='c1', version='1.0.0', content_id='1',
                                       dependencies={})
        dc_c1_other = CookbookPackageContent(name='c1', version='1.0.0', content_id='other',
                                             dependencies={})

        batch = [
            DeclarativeContent(content=dc_c1, d_artifacts=[]),
            DeclarativeContent(content=dc_c1_other, d_artifacts=[]),
        ]
        stage = QueryExistingContentUnits()
        stage._process_batch(batch)
        self.assertEqual(batch[0].content.content_id, '1')
        self.assertEqual(batch[0].content.pk, self.c1.pk)
        self.assertIsNone(batch[1].content.pk)

    def test_existing_content_is_ok(self):
        # dc_c1 is a duplicate of c1 existing in the DB
        dc_c1 = CookbookPackageContent(name='c1', version='1.0.0', content_id='1',
                                       dependencies={})
        c2 = CookbookPackageContent.objects.create(name='c2', version='1.0.0',
                                                   content_id='2', dependencies={})

        batch = [
            DeclarativeContent(content=dc_c1, d_artifacts=[]),
            DeclarativeContent(content=c2, d_artifacts=[]),
        ]
        stage = QueryExistingContentUnits()
        stage._process_batch(batch)
        self.assertEqual(batch[0].content.pk, self.c1.pk)
        self.assertEqual(batch[1].content.pk, c2.pk)


class QueryExistingRepoContentAndArtifactsTestCase(TestCase):
    """Verify that the QueryExistingRepoContentAndArtifacts properly associates from DB."""

    def setUp(self):
        self.remote = CookbookRemote.objects.create(name='remote')
        # c1: Existing content unit with Artifact a1
        self.a1 = Artifact.objects.create(size=0, sha256='1', sha384='1', sha512='1')
        self.c1 = CookbookPackageContent.objects.create(
            name='c1', version='1.0.0',
            content_id_type=CookbookPackageContent.SHA256,
            content_id='1',
            dependencies={}
        )
        self.c1.artifact = self.a1
        # c3: content unit does exist, has a content_artifact association,
        # but no artifact
        self.c3 = CookbookPackageContent.objects.create(
            name='c3', version='1.0.0',
            dependencies={}
        )
        self.c3.artifact = None

    def new_version_all_content(self):
        """Provide a mock for a repository version containing all content."""
        new_version = Mock()
        new_version.content = CookbookPackageContent.objects.all()
        return new_version

    def test_content_associated_using_repo_key(self):
        stage = QueryExistingRepoContentAndArtifacts(new_version=self.new_version_all_content())

        # c1: Existing content unit with Artifact
        c1 = CookbookPackageContent(name='c1', version='1.0.0',
                                    dependencies={})
        # c2: content unit does not exist in DB
        c2 = CookbookPackageContent(name='c2', version='1.0.0',
                                    dependencies={})
        # c3: content unit does exist, has a content_artifact association,
        # but no artifact (i.e. is a non-immediate content unit)
        c3 = CookbookPackageContent(name='c3', version='1.0.0',
                                    dependencies={})

        d_c1_d_a1 = DeclarativeArtifact(artifact=Artifact(),
                                        url='http://a1',
                                        relative_path=c1.relative_path(),
                                        remote=self.remote)
        d_c2_d_a2 = DeclarativeArtifact(artifact=Artifact(),
                                        url='http://a2',
                                        relative_path=c2.relative_path(),
                                        remote=self.remote)
        d_c3_d_a3 = DeclarativeArtifact(artifact=Artifact(),
                                        url='http://a3',
                                        relative_path=c3.relative_path(),
                                        remote=self.remote)

        batch = [
            DeclarativeContent(content=c1, d_artifacts=[d_c1_d_a1]),
            DeclarativeContent(content=c2, d_artifacts=[d_c2_d_a2]),
            DeclarativeContent(content=c3, d_artifacts=[d_c3_d_a3]),
        ]

        stage._process_batch(batch)

        self.assertEqual(batch[0].content.content_id, '1')
        self.assertEqual(batch[0].content.pk, self.c1.pk)
        self.assertEqual(batch[0].d_artifacts[0].artifact.pk, self.a1.pk)

        self.assertIsNone(batch[1].content.pk)
        self.assertIsNone(batch[1].d_artifacts[0].artifact.pk)

        self.assertEqual(batch[2].content.pk, self.c3.pk)
        self.assertIsNone(batch[2].d_artifacts[0].artifact.pk)
