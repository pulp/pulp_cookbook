User Setup
==========

Ansible Installer (Recommended)
-------------------------------

We recommend that you install `pulpcore` and `pulp-cookbook` together using the `Ansible installer
<https://github.com/pulp/pulp_installer/blob/master/README.md>`_. The remaining steps are all
performed by the installer and are not needed if you use it.

pip Install
-----------

This document assumes that you have `installed pulpcore
<https://docs.pulpproject.org/en/3.0/nightly/installation/instructions.html>`_
into a the virtual environment ``~/pulpvenv``.

Users should install from **either** PyPI or source.

From PyPI
*********

.. code-block:: bash

   sudo -u pulp -i
   source ~/pulpvenv/bin/activate
   pip install pulp-cookbook

From Source
***********

.. code-block:: bash

   sudo -u pulp -i
   source ~/pulpvenv/bin/activate
   git clone https://github.com/pulp/pulp_cookbook.git
   cd pulp_cookbook
   pip install -e .

Run Migrations
--------------

.. code-block:: bash

   export DJANGO_SETTINGS_MODULE=pulpcore.app.settings
   django-admin migrate cookbook

Run Services
------------

.. code-block:: bash

   django-admin runserver 24817
   gunicorn pulpcore.content:server --bind 'localhost:24816' --worker-class 'aiohttp.GunicornWebWorker' -w 2
   sudo systemctl restart pulpcore-resource-manager
   sudo systemctl restart pulpcore-worker@1
   sudo systemctl restart pulpcore-worker@2

