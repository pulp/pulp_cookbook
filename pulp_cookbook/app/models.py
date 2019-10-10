# (C) Copyright 2018 Simon Baatz <gmbnomis@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import uuid

from django.db import models

from pulpcore.plugin.models import Content, PublicationDistribution, Publication, Remote
from django.contrib.postgres.fields import JSONField


class CookbookPackageContent(Content):
    """
    The "cookbook" content type.

    Content of this type represents a Chef cookbook uniquely
    identified by name, version and content id.

    Fields:
        name (str): The name of the cookbook.
        version (str): The version of the cookbook.
        dependencies (JSON): The dependency information of the cookbook.
        content_id_type ('uuid' or 'sha256'): The type of the content_id field.
            'uuid' if the corresponding artifact is not known (yet). 'sha256'
            otherwise (the SHA256 digest of the corresponding artifact).
        content_id (str): The content id (random UUID or SHA256 digest of artifact)
    """

    # Constants for the choices of content_id types
    UUID = "uuid"
    SHA256 = "sha256"
    CONTENT_ID_TYPE_CHOICES = (
        (UUID, "On demand/streaming content: arbitrary UUID"),
        (SHA256, "Immediate download content: digest of associated artifact"),
    )

    TYPE = "cookbook"

    name = models.TextField(blank=False, null=False)
    version = models.TextField(blank=False, null=False)
    dependencies = JSONField(blank=False, null=False)
    content_id_type = models.CharField(
        max_length=10, choices=CONTENT_ID_TYPE_CHOICES, blank=False, null=False, default=UUID
    )
    content_id = models.CharField(max_length=64, null=False, blank=False, default=uuid.uuid4)

    def relative_path(self):
        return "{}-{}.tar.gz".format(self.name, self.version)

    @staticmethod
    def relative_path_from_data(data):
        return "{}-{}.tar.gz".format(data["name"], data["version"])

    def set_sha256_digest(self, sha256_digest):
        self.content_id_type = self.SHA256
        self.content_id = sha256_digest

    @classmethod
    def repo_key_fields(self):
        """
        Returns a tuple of the key fields that must be unique within a repository version.

        Returns:
            tuple: The repo key field names.

        """
        return ("name", "version")

    def repo_key_value(self):
        """
        Get the model's repo key based on repo_key_fields().

        Returns:
            tuple: The repo key.

        """
        return tuple(getattr(self, f) for f in self.repo_key_fields())

    def repo_key_dict(self):
        """
        Get the model's repo key as a dictionary of keys and values.

        Returns:
            dict: The repo key.

        """
        return {key: getattr(self, key) for key in self.repo_key_fields()}

    def repo_q(self):
        """
        Returns a Q object that represents the model within a repository version.
        """
        if not self._state.adding:
            return models.Q(pk=self.pk)
        return models.Q(**self.repo_key_dict())

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
        unique_together = ("name", "version", "content_id_type", "content_id")


class CookbookRemote(Remote):
    """
    Remote for "cookbook" content.
    """

    TYPE = "cookbook"

    cookbooks = JSONField(null=True)

    def specifier_cookbook_names(self):
        if self.cookbooks is None:
            return None
        else:
            return set(self.cookbooks.keys())

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class CookbookPublication(Publication):
    """
    Publication for 'cookbook' content.
    """

    TYPE = "cookbook"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class CookbookDistribution(PublicationDistribution):
    """
    Distribution for 'cookbook' content.
    """

    TYPE = "cookbook"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
