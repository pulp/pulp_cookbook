pulp-cookbook Plugin
====================

The ``cookbook`` plugin extends `pulpcore
<https://pypi.python.org/pypi/pulpcore/>`__ to support hosting Chef cookbooks.
This plugin assumes some familiarity with the `pulpcore documentation
<https://docs.pulpproject.org/en/3.0/nightly/>`_.

Currently, it allows to import packaged cookbooks into cookbook repositories.
When publishing a specific version of a cookbook repository, a `universe
<https://docs.chef.io/supermarket_api.html#universe>`_ endpoint will be created
to allow `berkshelf <https://docs.chef.io/berkshelf.html>`_ or `Policyfile
tooling <https://docs.chef.io/policyfile/>`_ to download cookbooks and resolve
cookbook dependencies.

**Not supported** (yet):

- Only the ``universe`` endpoint of the `Supermarket API
  <https://docs.chef.io/supermarket_api.html>`_ is implemented. For example, the
  ``knife supermarket`` commands do not work currently.

- Setting cookbook version constraints on a remote (only filtering by cookbook name
  is supported)

If you are just getting started, we recommend getting to know the :doc:`basic
workflows<workflows/index>`.

The REST API documentation for ``pulp_cookbook`` is available `here <restapi.html>`_.


Table of Contents
-----------------

.. toctree::
   :maxdepth: 1

   installation
   workflows/index
   restapi/index
   changes
   contributing


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

