from unittest.mock import Mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from pulpcore.plugin.models import Artifact, ContentArtifact

from pulp_cookbook.app.models import CookbookPackageContent
from pulp_cookbook.app.content import CookbookContentHandler


class CookbookContentHandlerTestCase(TestCase):
    """Test the CookbookContentHandler."""

    def setUp(self):
        self.c1 = CookbookPackageContent.objects.create(name='c1', version='1.0.0',
                                                        dependencies={})
        self.c1.artifact = None
        self.c1_prime = CookbookPackageContent.objects.create(name='c1', version='1.0.0',
                                                              dependencies={})
        self.c1_prime.artifact = None
        self.assertEqual(self.c1.content_id_type, CookbookPackageContent.UUID)
        self.assertEqual(self.c1_prime.content_id_type, CookbookPackageContent.UUID)

    def download_result_mock(self):
        dr = Mock()
        dr.artifact_attributes = {'size': 0}
        for digest_type in Artifact.DIGEST_FIELDS:
            dr.artifact_attributes[digest_type] = '1'
        dr.path = SimpleUploadedFile('c1', '')
        return dr

    def test_save_content_artifact(self):
        """Verify the 'on_demand' policy case."""
        cch = CookbookContentHandler()
        new_artifact = cch._save_content_artifact(self.download_result_mock(),
                                                  ContentArtifact.objects.get(pk=self.c1.pk))
        c1 = CookbookPackageContent.objects.get(pk=self.c1.pk)
        self.assertIsNotNone(new_artifact)
        self.assertEqual(c1.content_id, '1')
        self.assertEqual(c1._artifacts.get().sha256, '1')

    def test_save_content_artifact_artifact_already_exists(self):
        """Artifact turns out to already exist."""
        cch = CookbookContentHandler()
        new_artifact = cch._save_content_artifact(self.download_result_mock(),
                                                  ContentArtifact.objects.get(pk=self.c1.pk))
        c1 = CookbookPackageContent.objects.get(pk=self.c1.pk)
        self.assertIsNotNone(new_artifact)
        self.assertEqual(c1.content_id_type, CookbookPackageContent.SHA256)
        self.assertEqual(c1.content_id, '1')
        self.assertEqual(c1._artifacts.get().sha256, '1')

        existing_artifact = cch._save_content_artifact(self.download_result_mock(),
                                                       ContentArtifact.objects.get(pk=self.c1.pk))
        c1 = CookbookPackageContent.objects.get(pk=self.c1.pk)
        self.assertIsNotNone(existing_artifact)
        self.assertEqual(new_artifact.pk, existing_artifact.pk)
        self.assertEqual(c1.content_id_type, CookbookPackageContent.SHA256)
        self.assertEqual(c1.content_id, '1')
        self.assertEqual(c1._artifacts.get().sha256, '1')

    def test_save_content_artifact_other_content_exists(self):
        """When save tries to 'upgrade' the cookbook with the digest, failure is ignored."""
        CookbookPackageContent.objects.create(name='c1', version='1.0.0',
                                              content_id_type=CookbookPackageContent.SHA256,
                                              content_id='1',
                                              dependencies={})

        cch = CookbookContentHandler()
        new_artifact = cch._save_content_artifact(self.download_result_mock(),
                                                  ContentArtifact.objects.get(pk=self.c1.pk))
        c1 = CookbookPackageContent.objects.get(pk=self.c1.pk)
        self.assertIsNotNone(new_artifact)
        self.assertEqual(c1.content_id_type, CookbookPackageContent.UUID)
        self.assertEqual(c1.content_id, str(self.c1.content_id))
