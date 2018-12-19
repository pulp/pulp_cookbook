# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.db import models

from pulpcore.plugin.models import Content, ContentArtifact, Publisher, Remote
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
        return self._artifacts.get().pk

    @artifact.setter
    def artifact(self, artifact):
        if self.pk:
            ca = ContentArtifact(artifact=artifact,
                                 content=self,
                                 relative_path=self.relative_path())
            ca.save()

    def relative_path(self):
        return "{}-{}.tar.gz".format(self.name, self.version)

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

    cookbooks = JSONField(blank=True)

    def specifier_cookbook_names(self):
        if self.cookbooks == '':  # blank JSON field
            return None
        else:
            return set(self.cookbooks.keys())


class CookbookPublisher(Publisher):
    """
    Publisher for "cookbook" content.
    """

    TYPE = 'cookbook'
