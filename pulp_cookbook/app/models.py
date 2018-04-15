# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.db import models

from pulpcore.plugin.models import Content, ContentArtifact, Remote, Publisher
from pulpcore.plugin.fields import JSONField


class CookbookPackageContent(Content):
    """
    The "cookbook" content type.

    Content of this type represents a Chef cookbook uniquely
    identified by name and version.

    Fields:
        name (str): The name of the cookbook.
        version (str): The version of the cookbook.
        dependencies (JSON): The dependency information of the cookbook.
    """

    TYPE = 'cookbook'

    name = models.TextField(blank=False, null=False)
    version = models.TextField(blank=False, null=False)
    dependencies = JSONField(blank=False, null=False)

    @property
    def artifact(self):
        return self.artifacts.get().pk

    @artifact.setter
    def artifact(self, artifact):
        if self.pk:
            ca = ContentArtifact(artifact=artifact,
                                 content=self,
                                 relative_path="{}-{}.tar.gz".format(self.name, self.version))
            ca.save()

    class Meta:
        unique_together = (
            'name',
            'version'
        )


class CookbookRemote(Remote):
    """
    Remote for "cookbook" content.
    """
    TYPE = 'cookbook'


class CookbookPublisher(Publisher):
    """
    Publisher for "cookbook" content.
    """
    TYPE = 'cookbook'
