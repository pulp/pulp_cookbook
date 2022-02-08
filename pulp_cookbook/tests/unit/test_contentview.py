# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import base64
from django.contrib.auth.models import User
import hashlib

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, reset_queries
from django.test import TestCase
from django.test.utils import override_settings

from rest_framework.test import APIClient

from pulpcore.plugin.models import Artifact, ContentArtifact

from pulp_cookbook.app.models import CookbookPackageContent


class CookbookPackageContentViewSetTestCase(TestCase):
    """Test the CookbookPackageContentViewSet."""

    def setUp(self):
        # Create a content unit without an artifact
        self.c1_wo_art = CookbookPackageContent.objects.create(
            name="c_wo_artifact", version="1.0.0", dependencies={}
        )
        self.ca1_wo_art = ContentArtifact.objects.create(
            artifact=None, content=self.c1_wo_art, relative_path=self.c1_wo_art.relative_path()
        )
        # And 100 more with artifact (will result in two pages in the view)
        for i in range(100):
            sha256 = hashlib.sha256(str(i).encode()).hexdigest()
            self.a1 = Artifact.objects.create(
                size=0,
                sha224=hashlib.sha224(str(i).encode()).hexdigest(),
                sha256=sha256,
                sha384=hashlib.sha384(str(i).encode()).hexdigest(),
                sha512=hashlib.sha512(str(i).encode()).hexdigest(),
                file=SimpleUploadedFile("test_filename", b""),
            )
            self.c1 = CookbookPackageContent.objects.create(
                name="c1",
                version=f"{i}.0.0",
                content_id_type=CookbookPackageContent.SHA256,
                content_id=sha256,
                dependencies={},
            )
            ContentArtifact.objects.create(
                artifact=self.a1, content=self.c1, relative_path=self.c1.relative_path()
            )

    @override_settings(DEBUG=True)  # Set DEBUG to record connection.queries
    def test_content_viewset_list(self):
        User.objects.create_user(username="admin", password="admin", is_superuser=True)
        client = APIClient()
        auth_headers = {
            "HTTP_AUTHORIZATION": "Basic " + base64.b64encode(b"admin:admin").decode("ascii")
        }
        # Load all pages of the view
        next_url = "/pulp/api/v3/content/cookbook/cookbooks/"
        number_cookbooks = 0
        while next_url:
            reset_queries()
            content_result = client.get(next_url, **auth_headers).json()
            self.assertEqual(content_result["count"], 101)
            for content in content_result["results"]:
                number_cookbooks += 1
                if content["name"] == "c_wo_artifact":
                    self.assertIsNone(content["artifact"])
                else:
                    self.assertIsNotNone(content["artifact"])
            # 2 queries for authentication, 1 for content count, 1 for content, and 1
            # for the Artifact prefetch
            self.assertLessEqual(
                len(connection.queries), 5, msg=f"More than 5 queries:\n {connection.queries}"
            )
            next_url = content_result["next"]
        self.assertEqual(number_cookbooks, 101)
