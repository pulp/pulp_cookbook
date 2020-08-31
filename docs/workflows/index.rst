.. _workflows-index:

Workflows
=========

If you have not yet installed the `cookbook` plugin on your Pulp installation,
please follow our :doc:`../installation`. These documents will assume you have
the environment installed and ready to go.

The REST API examples here use `httpie <https://httpie.org/doc>`_ to perform the
requests. The ``httpie`` commands below assume that the user executing the
commands has a ``.netrc`` file in the home directory. The ``.netrc`` should have
the following configuration:

.. code-block:: text

    machine localhost
    login admin
    password admin

If you configured the ``admin`` user with a different password, adjust the
configuration accordingly. If you prefer to specify the username and password
with each request, please see ``httpie`` documentation on how to do that.

To make these workflows copy/pastable, we make use of environment variables. The
first variable to set is the hostname and port::

   $ export BASE_ADDR=http://<hostname>:24817

This documentation makes use of the `jq <https://stedolan.github.io/jq/>`_ tool
to parse the json received from requests, in order to get the unique urls
generated when objects are created. To follow this documentation as-is please
install the jq library/binary with:

``$ sudo dnf install jq``

Scripting
---------

The workflows use bash functions that wait for the completion of a Pulp task if
necessary. These are defined in :download:`docs/_scripts/base.sh
<../_scripts/base.sh>`:

.. literalinclude:: ../_scripts/base.sh
   :language: bash

To execute the examples given in the workflows (and to develop own workflows), source ``base.sh`` first:

``source docs/_script/base.sh``

.. toctree::
   :maxdepth: 2

   sync
   upload
   publish
   supermarket_snapshot
