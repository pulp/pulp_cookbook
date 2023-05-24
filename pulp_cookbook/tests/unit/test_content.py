# (C) Copyright 2019 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import pytest
import uuid
from unittest.mock import Mock

from pulpcore.plugin.models import Artifact, ContentArtifact, RemoteArtifact
from pulpcore.plugin.content import Handler

from pulp_cookbook.app.models import CookbookPackageContent, CookbookRemote
from pulp_cookbook.app.content import CookbookContentHandler


@pytest.fixture
def remote(db):
    return CookbookRemote.objects.create(name="remote")


@pytest.fixture
def c1(db):
    return CookbookPackageContent.objects.create(name="c1", version="1.0.0", dependencies={})


@pytest.fixture
def ca1(c1):
    return ContentArtifact.objects.create(
        artifact=None, content=c1, relative_path=c1.relative_path()
    )


@pytest.fixture
def ra1(ca1, remote):
    return RemoteArtifact.objects.create(content_artifact=ca1, remote=remote)


@pytest.fixture
def c1_prime(db):
    return CookbookPackageContent.objects.create(name="c1", version="1.0.0", dependencies={})


def test_content_id_type(c1, c1_prime):
    assert c1.content_id_type == CookbookPackageContent.UUID
    assert c1_prime.content_id_type == CookbookPackageContent.UUID


def test_save_artifact(c1, ra1, monkeypatch):
    """Verify the 'on_demand' policy case."""
    _save_artifact = Mock()
    _save_artifact.return_value = Artifact(sha256="1")
    monkeypatch.setattr(Handler, "_save_artifact", _save_artifact)

    cch = CookbookContentHandler()
    # Do not use the in-memory version of ra1!
    new_artifact = cch._save_artifact(None, RemoteArtifact.objects.get(pk=ra1.pk))
    c1 = CookbookPackageContent.objects.get(pk=c1.pk)
    assert new_artifact is not None
    assert c1.content_id == "1"


def test_save_artifact_other_content_exists(c1, ra1, monkeypatch):
    """When save tries to 'upgrade' the cookbook with the digest, failure is ignored."""
    _save_artifact = Mock()
    _save_artifact.return_value = Artifact(sha256="1")
    monkeypatch.setattr(Handler, "_save_artifact", _save_artifact)

    CookbookPackageContent.objects.create(
        name="c1",
        version="1.0.0",
        content_id_type=CookbookPackageContent.SHA256,
        content_id="1",
        dependencies={},
    )

    cch = CookbookContentHandler()
    # Do not use the in-memory version of ra1!
    new_artifact = cch._save_artifact(None, RemoteArtifact.objects.get(pk=ra1.pk))
    refreshed_c1 = CookbookPackageContent.objects.get(pk=c1.pk)
    assert new_artifact is not None
    assert refreshed_c1.content_id_type == CookbookPackageContent.UUID
    assert refreshed_c1.content_id == str(c1.content_id)
