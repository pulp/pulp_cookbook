.. _supermarket-snapshot:

Snapshot of Chef Supermarket
============================

Using the 'on_demand' policy on a remote allows to create snapshots of a large
repository like the Chef Supermarket effectively. In "on_demand" mode, only the
meta-data will be synchronized. Actual cookbooks are not downloaded at sync
time, but only when requested from a distribution.

The coobook versions distributed are the ones that were presents during the
sync, i.e. this will create a frozen snapshot of the Chef Supermarket. Thanks to
the repository versioning feature of Pulp 3, you can create a new repository
version (i.e. a new snapshot) by syncing the Chef Supermarket at a later time.
Note that this does neither influence existing repository versions nor existing
distributions. This new repository version will become visible only after
publishing and updating the distribution accordingly.

Create a Remote ``supermarket``
-------------------------------

Using `policy=on_demand` for the remote enables "lazy download": A sync using
this remote will download the metadata from the Chef Supermarket (i.e.
information about all cookbooks and their respective versions), but no actual
cookbook tar files.

Cookbooks will be downloaded only when requested from a distribution. After the
first successful download, the cookbooks are stored locally for faster
retrieval.

.. literalinclude:: ../_scripts/create_remote_supermarket.sh
   :language: bash

Response:

.. literalinclude:: ../_snippets/create_remote_supermarket.txt
   :language: json

Create a repository ``supermarket``
-----------------------------------

If you don't already have a repository called ``supermarket``, create one using
the remote just created as its default remote:

.. literalinclude:: ../_scripts/create_repo_supermarket.sh
   :language: bash

Response:

.. literalinclude:: ../_snippets/create_repo_supermarket.txt
   :language: json


Sync repository ``supermarket``
-------------------------------

Use the repository object to kick off a synchronize task. You are telling pulp
to fetch content from the default remote stored in the repository and mirror the
current content exactly (``mirror:=true``):

.. literalinclude:: ../_scripts/sync_repo_supermarket.sh
   :language: bash


Response (finished task status):

.. literalinclude:: ../_snippets/sync_repo_supermarket.txt
   :language: json


Create a Publication
--------------------

The sync created a new repository version which is reflected in the
"latest_version_href" field of the repository.

You can kick off a publish task by specifying the repository version to publish.
Alternatively, you can specify repository, which will publish the latest
version.

The result of a publish is a publication, which contains all the information
needed for an external package manager like ``berkshelf`` to use.
Publications are not consumable until they are hosted by a distribution:

.. literalinclude:: ../_scripts/create_publication_supermarket.sh
   :language: bash


Response (finished task status):

.. literalinclude:: ../_snippets/create_publication_supermarket.txt
   :language: json


Create a Distribution at 'supermarket' for the Publication
----------------------------------------------------------

To host a publication, you create a distribution which will serve the associated
publication at ``/pulp_cookbook/content/<distribution.base_path>``. In the
example, ``base_path`` is set to ``supermarket``.

.. literalinclude:: ../_scripts/create_distribution_supermarket.sh
   :language: bash


Response (finished task status):

.. literalinclude:: ../_snippets/create_distribution_supermarket.txt
   :language: json


You can have a look at the published "universe" metadata now:

``$ http localhost:24816/pulp_cookbook/content/supermarket/universe``

In your ``Berksfile``, you can use the following ``source`` to access the
Supermarket snapshot:

.. code:: ruby

   source 'http://localhost/pulp_cookbook/content/supermarket/'
