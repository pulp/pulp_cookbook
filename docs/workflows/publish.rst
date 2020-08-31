
Publish and Host
================

This section assumes that you have a repository called ``foo`` with content in it. To do this, see the
:doc:`sync` or :doc:`upload` documentation.

Create a Publication
--------------------

Create a publication from the latest repository version. This prepares the
meta-data needed to distribute the content of the repository on a ``/universe``
endpoint. However, creating a publication distributes no content to the outside.
This has to be done in a separate step.

.. literalinclude:: ../_scripts/create_publication_foo.sh
   :language: bash

Response:

.. literalinclude:: ../_snippets/create_publication_foo.txt
   :language: json


Create a Distribution ``foo`` for the Publication
-------------------------------------------------

Actually distribute the publication created in the last step at a specific path.
The base path is ``foo`` in this case. The publication will be distributed at
``/pulp_cookbook/content/foo/universe`` on the content endpoint (which is on
port 24816 in our example).

.. literalinclude:: ../_scripts/create_distribution_foo.sh
   :language: bash

Response:

.. literalinclude:: ../_snippets/create_distribution_foo.txt
   :language: json


You can have a look at the published "universe" metadata now:

.. literalinclude:: ../_scripts/get_universe_foo.sh
   :language: bash

Response:

.. literalinclude:: ../_snippets/get_universe_foo.txt
   :language: json


Use Berkshelf with the published repo
-------------------------------------

Create a ``Berksfile`` with the following content:


.. literalinclude:: ../_scripts/Berksfile
   :language: ruby


And run:

``$ berks install``

.. code:: text

   Resolving cookbook dependencies...
   Fetching cookbook index from http://localhost:24816/pulp_cookbook/content/foo/...
   Installing apt (7.0.0) from http://localhost:24816/pulp_cookbook/content/foo/ ([uri] http://localhost:24816/pulp_cookbook/content/foo/cookbook_files/apt/7_0_0/apt-7.0.0.tar.gz)
   Installing ubuntu (2.0.1) from http://localhost:24816/pulp_cookbook/content/foo/ ([uri] http://localhost:24816/pulp_cookbook/content/foo/cookbook_files/ubuntu/2_0_1/ubuntu-2.0.1.tar.gz)
