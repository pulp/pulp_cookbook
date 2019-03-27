# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from unittest.mock import patch

from django.test import TestCase

from pulpcore.plugin.models import Artifact, ContentArtifact, RemoteArtifact
from pulpcore.plugin.content import Handler

from pulp_cookbook.app.models import CookbookPackageContent, CookbookRemote
from pulp_cookbook.app.content import CookbookContentHandler


class CookbookContentHandlerTestCase(TestCase):
    """Test the CookbookContentHandler."""

    def setUp(self):
        self.remote = CookbookRemote.objects.create(name="remote")

        self.c1 = CookbookPackageContent.objects.create(name="c1", version="1.0.0", dependencies={})
        self.ca1 = ContentArtifact.objects.create(
            artifact=None, content=self.c1, relative_path=self.c1.relative_path()
        )
        self.ra1 = RemoteArtifact.objects.create(content_artifact=self.ca1, remote=self.remote)
        self.c1_prime = CookbookPackageContent.objects.create(
            name="c1", version="1.0.0", dependencies={}
        )
        self.ca1_prime = ContentArtifact.objects.create(
            artifact=None, content=self.c1_prime, relative_path=self.c1_prime.relative_path()
        )
        self.ra1_prime = RemoteArtifact.objects.create(
            content_artifact=self.ca1_prime, remote=self.remote
        )
        self.assertEqual(self.c1.content_id_type, CookbookPackageContent.UUID)
        self.assertEqual(self.c1_prime.content_id_type, CookbookPackageContent.UUID)

    @patch.object(Handler, "_save_artifact", return_value=Artifact(sha256="1"))
    def test_save_artifact(self, save_artifact_mock):
        """Verify the 'on_demand' policy case."""
        cch = CookbookContentHandler()
        new_artifact = cch._save_artifact(None, RemoteArtifact.objects.get(pk=self.ra1.pk))
        c1 = CookbookPackageContent.objects.get(pk=self.c1.pk)
        self.assertIsNotNone(new_artifact)
        self.assertEqual(c1.content_id, "1")

    @patch.object(Handler, "_save_artifact", return_value=Artifact(sha256="1"))
    def test_save_artifact_other_content_exists(self, save_artifact_mock):
        """When save tries to 'upgrade' the cookbook with the digest, failure is ignored."""
        CookbookPackageContent.objects.create(
            name="c1",
            version="1.0.0",
            content_id_type=CookbookPackageContent.SHA256,
            content_id="1",
            dependencies={},
        )

        cch = CookbookContentHandler()
        new_artifact = cch._save_artifact(None, RemoteArtifact.objects.get(pk=self.ra1.pk))
        c1 = CookbookPackageContent.objects.get(pk=self.c1.pk)
        self.assertIsNotNone(new_artifact)
        self.assertEqual(c1.content_id_type, CookbookPackageContent.UUID)
        self.assertEqual(c1.content_id, str(self.c1.content_id))
