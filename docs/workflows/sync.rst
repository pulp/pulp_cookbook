Synchronize a Repository
========================

Users can populate their repositories with content from an external sources by syncing
their repository.

Bear in mind that the attached snippets utilize ``pulp_http``. Refer to
:ref:`workflows-index` to learn more about these utilities and the required
tools (``httpie`` and ``jq``).

Create a Remote
---------------

In addition to :ref:`uploading content <workflows-upload>`, ``pulp_cookbook``
allows to synchronize a repository with an external content source (that has to
provide a "universe" endpoint, like the Chef Supermarket). Creating a remote
object informs Pulp about an external content source.

Since the Chef Supermarket is huge, let's mirror only the ``pulp``, ``qpid``,
and ``ubuntu`` cookbooks into our repository by setting the ``cookbooks``
parameter. First, we have to create a remote:

.. literalinclude:: ../_scripts/create_remote_foo.sh
   :language: bash

Response:

.. literalinclude:: ../_snippets/create_remote_foo.txt
   :language: json

Create a Repository
-------------------

If you don't already have a repository called ``foo``, create one. While it is
possible to add the remote as a parameters to every sync operation, it is more
convenient to store the default remote in the repository:

.. literalinclude:: ../_scripts/create_repo_foo_with_remote.sh
   :language: bash

Response:

.. literalinclude:: ../_snippets/create_repo_foo_with_remote.txt
   :language: json


Sync repository ``foo``
-----------------------

Use the repository object to kick off a synchronize task. You are telling pulp
to fetch content from the default remote stored with the repository and add to
the latest repository version (``mirror:=false``):


.. literalinclude:: ../_scripts/sync_repo_foo.sh
   :language: bash


Response (finished task status):

.. literalinclude:: ../_snippets/sync_repo_foo.txt
   :language: json

When the synchronize task completes successfully, there are two possible outcomes:

1. If the sync changed the content, it creates a new version, which is
   specified in ``created_resources``. Moreover, the created repository version
   will become the ``latest_version`` of the repository.
2. If the sync did not change the content (i.e. the remote contains no
   changes compared to the current repository version), no new version is
   created and ``created_resources`` is empty.

You can have a look at the latest repository version:


.. literalinclude:: ../_scripts/get_latest_version_foo.sh
   :language: bash


Response:

.. literalinclude:: ../_snippets/get_latest_version_foo.txt
   :language: json
