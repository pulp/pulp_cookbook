.. image:: https://travis-ci.org/gmbnomis/pulp_cookbook.svg?branch=master
   :target: https://travis-ci.org/gmbnomis/pulp_cookbook
   :alt: Travis (.org)
.. image:: https://img.shields.io/pypi/v/pulp-cookbook.svg
   :target: https://pypi.python.org/pypi/pulp-cookbook
   :alt: PyPI
.. image:: https://img.shields.io/pypi/pyversions/pulp-cookbook.svg
   :target: https://pypi.python.org/pypi/pulp-cookbook
   :alt: PyPI - Python Version


``pulp_cookbook`` Plugin
========================

This is the ``pulp_cookbook`` Plugin for `Pulp Project 3.0+
<https://pypi.python.org/pypi/pulpcore/>`__. This plugin implements
support for Chef cookbooks.

Currently, it allows to import packaged cookbooks into cookbook
repositories. When publishing a specific version of a cookbook
repository, a `universe
<https://docs.chef.io/supermarket_api.html#universe>`_ endpoint will
be created to allow tools like `berkshelf
<https://docs.chef.io/berkshelf.html>`_ to download cookbooks and
resolve cookbook dependencies.

**Not supported** (yet):

- Full support of the `Supermarket API <https://docs.chef.io/supermarket_api.html>`_
- Cookbook version constraints to a remote (only filtering by cookbook name
  is supported)

All REST API examples below use `httpie <https://httpie.org/doc>`__ to perform
the requests. The ``httpie`` commands below assume that the user executing the
commands has a ``.netrc`` file in the home directory. The ``.netrc`` should have
the following configuration:

.. code:: text

    machine localhost
    login admin
    password admin

If you configured the ``admin`` user with a different password, adjust the
configuration accordingly. If you prefer to specify the username and password
with each request, please see ``httpie`` documentation on how to do that.

This documentation makes use of the `jq library
<https://stedolan.github.io/jq/>`_ to parse the json received from requests, in
order to get the unique urls generated when objects are created. To follow this
documentation as-is please install the jq library/binary with:

``$ sudo dnf install jq``


Install ``pulpcore``
--------------------

Follow the `installation
instructions <https://docs.pulpproject.org/en/3.0/nightly/installation/instructions.html>`__
provided with pulpcore.

Users should install from **either** PyPI or source.

Install ``pulp_cookbook`` from source
-------------------------------------

.. code-block:: bash

   sudo -u pulp -i
   source ~/pulpvenv/bin/activate
   git clone https://github.com/gmbnomis/pulp_cookbook.git
   cd pulp_cookbook
   pip install -e .

Install ``pulp-cookbook`` From PyPI
-----------------------------------

.. code-block:: bash

   sudo -u pulp -i
   source ~/pulpvenv/bin/activate
   pip install pulp-cookbook

Make and Run Migrations
-----------------------

.. code-block:: bash

   export DJANGO_SETTINGS_MODULE=pulpcore.app.settings
   django-admin makemigrations pulp_cookbook
   django-admin migrate pulp_cookbook

Run Services
------------

.. code-block:: bash

   django-admin runserver 24817
   gunicorn pulpcore.content:server --bind 'localhost:24816' --worker-class 'aiohttp.GunicornWebWorker' -w 2
   sudo systemctl restart pulp-resource-manager
   sudo systemctl restart pulp-worker@1
   sudo systemctl restart pulp-worker@2

Example: Import cookbooks and synchronize from remote
=====================================================

Create a repository ``foo``
---------------------------

``$ http POST http://localhost:24817/pulp/api/v3/repositories/ name=foo``

.. code:: json

    {
        "_created": "2019-03-30T22:33:45.622911Z",
        "_href": "/pulp/api/v3/repositories/4782fa5b-c36e-4a24-867d-5965525609e3/",
        "_latest_version_href": null,
        "_versions_href": "/pulp/api/v3/repositories/4782fa5b-c36e-4a24-867d-5965525609e3/versions/",
        "description": "",
        "name": "foo"
    }

``$ export REPO_HREF=$(http :24817/pulp/api/v3/repositories/ | jq -r '.results[] | select(.name == "foo") | ._href')``

Upload cookbooks to Pulp
------------------------

As a simple example, let's download two cookbooks from the Chef Supermarket and
upload them into our repository.

Download 'ubuntu' and 'apt' cookbooks (the 'ubuntu' cookbooks depends on the
'apt' cookbook):

``$ curl -Lo ubuntu-2.0.1.tgz https://supermarket.chef.io:443/api/v1/cookbooks/ubuntu/versions/2.0.1/download``
``$ curl -Lo apt-7.0.0.tgz https://supermarket.chef.io:443/api/v1/cookbooks/apt/versions/7.0.0/download``


Create artifacts by uploading the cookbooks to Pulp. First, the artifact for the
"ubuntu" cookbook:

.. code:: bash

    ubuntu_resp=$(http --form POST http://localhost:24817/pulp/api/v3/artifacts/ file@ubuntu-2.0.1.tgz)
    echo "$ubuntu_resp" | jq .
    export UBUNTU_ARTIFACT_HREF=$(echo "$ubuntu_resp" | jq -r '._href')


.. code:: json

    {
    "_href": "/pulp/api/v3/artifacts/f1469706-e8fe-4ecd-80d1-60a55b4f828c/",
    "_created": "2019-03-30T22:34:36.926220Z",
    "file": "artifact/32/a7d3de4ff8f769eeab4ffc982eb8df845d91d49c01548d6f993b10e52b6f69",
    "size": 3712,
    "md5": "36b2b6e59dfd4ce8185042e384d73498",
    "sha1": "e66700968de9441266e48178acfe63f605d04101",
    "sha224": "60807a9415be340a0eaab792c85c0b143f48d18ee82a9e3774c82d18",
    "sha256": "32a7d3de4ff8f769eeab4ffc982eb8df845d91d49c01548d6f993b10e52b6f69",
    "sha384": "2c5ce13bce99a1f9321d52b7cd9e8a8f4388c7def8b6f977ba6a095bf68e723c4053b5b8687609fb26c8e5e06ec88f84",
    "sha512": "b9311176f3cad3aad486717f96ed6a87e520fceb03f389dc5980499ebcef0388acea2106fe964a2e411f39abfbf194d56b96825d7befaef7d3ebbeeb0f5b4c6c"
    }

And then, the "apt" cookbook:

.. code:: bash

    apt_resp=$(http --form POST http://localhost:24817/pulp/api/v3/artifacts/ file@apt-7.0.0.tgz)
    echo "$apt_resp" | jq .
    export APT_ARTIFACT_HREF=$(echo "$apt_resp" | jq -r '._href')

Create ``cookbook`` content from an Artifact
--------------------------------------------

Create a content unit for ubuntu 2.0.1:

``$ http POST http://localhost:24817/pulp/api/v3/content/cookbook/cookbooks/ name="ubuntu" _artifact="$UBUNTU_ARTIFACT_HREF"``

.. code:: json

    {
        "_artifact": "/pulp/api/v3/artifacts/f1469706-e8fe-4ecd-80d1-60a55b4f828c/",
        "_created": "2019-03-30T22:36:05.331407Z",
        "_href": "/pulp/api/v3/content/cookbook/cookbooks/2ee7a09b-bfde-4d3c-a1bf-fc2a327fd15a/",
        "_type": "cookbook.cookbook",
        "content_id": "32a7d3de4ff8f769eeab4ffc982eb8df845d91d49c01548d6f993b10e52b6f69",
        "dependencies": {
            "apt": ">= 0.0.0"
        },
        "name": "ubuntu",
        "version": "2.0.1"
    }

``$ export UBUNTU_CONTENT_HREF=$(http :24817/pulp/api/v3/content/cookbook/cookbooks/?name=ubuntu | jq -r '.results[0]._href')``

Create a content unit for apt 7.0.0:

``$ http POST http://localhost:24817/pulp/api/v3/content/cookbook/cookbooks/ name="apt" _artifact="$APT_ARTIFACT_HREF"``

.. code:: json

    {
        "_artifact": "/pulp/api/v3/artifacts/250b94e1-2b6a-4de8-a8c5-0e27d56f4687/",
        "_created": "2019-03-30T22:36:46.013134Z",
        "_href": "/pulp/api/v3/content/cookbook/cookbooks/f5bde692-a440-4bf7-a873-1465c68c0932/",
        "_type": "cookbook.cookbook",
        "content_id": "c1953292327871542d97a31989ff745c49f610c0f1a16b147d59bc4a60f6e7cd",
        "dependencies": {},
        "name": "apt",
        "version": "7.0.0"
    }

``$ export APT_CONTENT_HREF=$(http :24817/pulp/api/v3/content/cookbook/cookbooks/?name=apt | jq -r '.results[0]._href')``


Add content to repository ``foo``
---------------------------------

``$ http POST :24817$REPO_HREF'versions/' add_content_units:="[\"$UBUNTU_CONTENT_HREF\",\"$APT_CONTENT_HREF\"]"``


Create a ``cookbook`` Publisher
-------------------------------

``$ http POST http://localhost:24817/pulp/api/v3/publishers/cookbook/cookbook/ name=publisher``


.. code:: json

    {
        "_created": "2019-03-30T22:37:31.851159Z",
        "_distributions": [],
        "_href": "/pulp/api/v3/publishers/cookbook/cookbook/a985c28b-c7be-4e66-b10e-d3f799c23726/",
        "_last_updated": "2019-03-30T22:37:31.851227Z",
        "_type": "cookbook.cookbook",
        "name": "publisher"
    }

``$ export PUBLISHER_HREF=$(http :24817/pulp/api/v3/publishers/cookbook/cookbook/ | jq -r '.results[] | select(.name == "publisher") | ._href')``


Use the ``publisher`` Publisher to create a Publication
-------------------------------------------------------

``$ http POST :24817$PUBLISHER_HREF'publish/' repository=$REPO_HREF``

.. code:: json

    {
        "task": "/pulp/api/v3/tasks/2/"
    }

``$ export PUBLICATION_HREF=$(http :24817/pulp/api/v3/publications/ | jq -r --arg PUBLISHER_HREF "$PUBLISHER_HREF" '.results[] | select(.publisher==$PUBLISHER_HREF) | ._href')``


Create a Distribution at 'foo' for the Publication
--------------------------------------------------

``$ http POST http://localhost:24817/pulp/api/v3/distributions/ name='baz' base_path='foo' publication=$PUBLICATION_HREF``

You can have a look at the published "universe" metadata now:

``$ http http://localhost:24816/pulp_cookbook/content/foo/universe``

.. code:: json

    {
        "apt": {
            "7.0.0": {
                "dependencies": {},
                "download_url": "http://localhost:24816/pulp_cookbook/content/foo/cookbook_files/apt/7_0_0/apt-7.0.0.tar.gz",
                "location_path": "http://localhost:24816/pulp_cookbook/content/foo/cookbook_files/apt/7_0_0/apt-7.0.0.tar.gz",
                "location_type": "uri"
            }
        },
        "ubuntu": {
            "2.0.1": {
                "dependencies": {
                    "apt": ">= 0.0.0"
                },
                "download_url": "http://localhost:24816/pulp_cookbook/content/foo/cookbook_files/ubuntu/2_0_1/ubuntu-2.0.1.tar.gz",
                "location_path": "http://localhost:24816/pulp_cookbook/content/foo/cookbook_files/ubuntu/2_0_1/ubuntu-2.0.1.tar.gz",
                "location_type": "uri"
            }
        }
    }


Use Berkshelf with the published repo
-------------------------------------

Create a Berksfile with the following content:


.. code:: ruby

   source 'http://localhost:24816/pulp_cookbook/content/foo/'

   cookbook 'ubuntu'


``$ berks install``

.. code:: text

   Resolving cookbook dependencies...
   Fetching cookbook index from http://localhost:24816/pulp_cookbook/content/foo/...
   Installing apt (7.0.0) from http://localhost:24816/pulp_cookbook/content/foo/ ([uri] http://localhost:24816/pulp_cookbook/content/foo/cookbook_files/apt/7_0_0/apt-7.0.0.tar.gz)
   Installing ubuntu (2.0.1) from http://localhost:24816/pulp_cookbook/content/foo/ ([uri] http://localhost:24816/pulp_cookbook/content/foo/cookbook_files/ubuntu/2_0_1/ubuntu-2.0.1.tar.gz)

Create a new remote ``foo_remote``
-----------------------------------

In addition to uploading content, ``pulp_cookbook`` allows to synchronize a repo
with an upstream repo (that has to provide a "universe" endpoint).

Let's mirror the ``pulp`` and ``qpid`` cookbooks into our existing repo. First, we have to create a remote:

``$ http POST http://localhost:24817/pulp/api/v3/remotes/cookbook/cookbook/ name='foo_remote' url='https://supermarket.chef.io/' cookbooks:='{"pulp": "", "qpid": ""}'``

.. code:: json

    {
        "_created": "2019-03-30T22:39:23.020585Z",
        "_href": "/pulp/api/v3/remotes/cookbook/cookbook/2ccb7aed-1625-419f-bf4a-8dce87c43b63/",
        "_last_updated": "2019-03-30T22:39:23.020603Z",
        "_type": "cookbook.cookbook",
        "cookbooks": {
            "pulp": "",
            "qpid": ""
        },
        "download_concurrency": 20,
        "name": "foo_remote",
        "policy": "immediate",
        "proxy_url": "",
        "ssl_validation": true,
        "url": "https://supermarket.chef.io/",
        "validate": true
    }

``$ export REMOTE_HREF=$(http :24817/pulp/api/v3/remotes/cookbook/cookbook/ | jq -r '.results[] | select(.name == "foo_remote") | ._href')``

Sync repository ``foo`` using remote ``foo_remote``
----------------------------------------------------

We don't want to delete the ``apt`` and ``ubuntu`` coobooks imported previously.
Therefore, we sync in 'additive' mode by setting ``mirror`` to false.

``$ http POST :24817$REMOTE_HREF'sync/' repository=$REPO_HREF mirror:=false``

Look at the new Repository Version created
------------------------------------------

``$ http GET ':24817'$REPO_HREF'versions/2/'``

.. code:: json

    {
        "_created": "2019-03-30T22:40:09.204067Z",
        "_href": "/pulp/api/v3/repositories/4782fa5b-c36e-4a24-867d-5965525609e3/versions/2/",
        "base_version": null,
        "content_summary": {
            "added": {
                "cookbook.cookbook": {
                    "count": 2,
                    "href": "/pulp/api/v3/content/cookbook/cookbooks/?repository_version_added=/pulp/api/v3/repositories/4782fa5b-c36e-4a24-867d-5965525609e3/versions/2/"
                }
            },
            "present": {
                "cookbook.cookbook": {
                    "count": 4,
                    "href": "/pulp/api/v3/content/cookbook/cookbooks/?repository_version=/pulp/api/v3/repositories/4782fa5b-c36e-4a24-867d-5965525609e3/versions/2/"
                }
            },
            "removed": {}
        },
        "number": 2
    }

At the time of writing, there was only a single version of the ``pulp`` and
``qpid`` cookbooks available, respectively. This brings the total count to 4 cookbooks.

Publish the newest version
--------------------------

To publish the version just created, do:

``$ http POST :24817$PUBLISHER_HREF'publish/' repository=$REPO_HREF``

And update the distribution:

.. code:: bash

    export DISTRIBUTION_HREF=$(http :24817/pulp/api/v3/distributions/ | jq -r '.results[] | select(.name == "baz") | ._href')
    export LATEST_VERSION_HREF=$(http :24817$REPO_HREF | jq -r '._latest_version_href')
    export LATEST_PUBLICATION_HREF=$(http :24817/pulp/api/v3/publications/ | jq --arg LVH "$LATEST_VERSION_HREF" -r '.results[] | select(.repository_version == $LVH) | ._href')
    http PATCH :24817$DISTRIBUTION_HREF publication=$LATEST_PUBLICATION_HREF

Now, the universe endpoint
``http://localhost:24816/pulp_cookbook/content/foo/universe`` will show the
content of the new repo version.


Example: Snapshot of Chef Supermarket
=====================================

Using the 'on_demand' policy on a remote allows to create snapshots of a large
repo like the Chef Supermarket effectively. In "on_demand" mode, only the
meta-data will be synchronized. Actual cookbooks are not downloaded at sync
time, but only when requested from a distribution. After the first successful
download, the cookbooks are stored locally for faster retrieval.

Create a repository ``supermarket``
-----------------------------------

``$ http POST http://localhost:24817/pulp/api/v3/repositories/ name=supermarket``

.. code:: json

    {
        "_created": "2019-03-30T22:59:02.569833Z",
        "_href": "/pulp/api/v3/repositories/80f03582-ae58-406d-b456-bbb33e718f8f/",
        "_latest_version_href": null,
        "_versions_href": "/pulp/api/v3/repositories/80f03582-ae58-406d-b456-bbb33e718f8f/versions/",
        "description": "",
        "name": "supermarket"
    }


``$ export REPO_HREF=$(http :24817/pulp/api/v3/repositories/ | jq -r '.results[] | select(.name == "supermarket") | ._href')``


Create a new remote ``supermarket``
-----------------------------------

``$ http POST http://localhost:24817/pulp/api/v3/remotes/cookbook/cookbook/ name='supermarket' url='https://supermarket.chef.io/' policy=on_demand``

.. code:: json

    {
        "_created": "2019-03-30T22:59:35.618466Z",
        "_href": "/pulp/api/v3/remotes/cookbook/cookbook/472c73b9-0132-4c1b-8814-816fd237a40a/",
        "_last_updated": "2019-03-30T22:59:35.618484Z",
        "_type": "cookbook.cookbook",
        "cookbooks": "",
        "download_concurrency": 20,
        "name": "supermarket",
        "policy": "on_demand",
        "proxy_url": "",
        "ssl_validation": true,
        "url": "https://supermarket.chef.io/",
        "validate": true
    }


``$ export REMOTE_HREF=$(http :24817/pulp/api/v3/remotes/cookbook/cookbook/ | jq -r '.results[] | select(.name == "supermarket") | ._href')``


Sync repository ``supermarket`` using remote ``supermarket``
------------------------------------------------------------


``$ http POST :24817$REMOTE_HREF'sync/' repository=$REPO_HREF mirror:=true``

.. code:: json

    {
        "task": "/pulp/api/v3/tasks/24990466-6602-4f4f-bb59-6d827bd48130/"
    }

This will take a while. You can query the task status using the returned URL. In
the example above, use ``http
:24817/pulp/api/v3/tasks/24990466-6602-4f4f-bb59-6d827bd48130/`` and inspect the
"state" field.


Create a ``supermarket`` Publisher
----------------------------------

``$ http POST http://localhost:24817/pulp/api/v3/publishers/cookbook/cookbook/ name=supermarket``

.. code:: json

    {
        "_created": "2019-03-30T23:01:44.703651Z",
        "_distributions": [],
        "_href": "/pulp/api/v3/publishers/cookbook/cookbook/b9df1aef-8eda-4370-8199-93539f14455e/",
        "_last_updated": "2019-03-30T23:01:44.703671Z",
        "_type": "cookbook.cookbook",
        "name": "supermarket"
    }


``$ export PUBLISHER_HREF=$(http :24817/pulp/api/v3/publishers/cookbook/cookbook/ | jq -r '.results[] | select(.name == "supermarket") | ._href')``


Use the ``supermarket`` Publisher to create a Publication
---------------------------------------------------------

``$ http POST :24817$PUBLISHER_HREF'publish/' repository=$REPO_HREF``

.. code:: json

    {
        "task": "/pulp/api/v3/tasks/8e9d3faf-695f-4048-a11a-1a7a65bd2f8e/"
    }

Again, this may take some time. When the task is finished, get the URL of the
publication:

``$ export PUBLICATION_HREF=$(http :24817/pulp/api/v3/publications/ | jq -r --arg PUBLISHER_HREF "$PUBLISHER_HREF" '.results[] | select(.publisher==$PUBLISHER_HREF) | ._href')``


Create a Distribution at 'supermarket' for the Publication
----------------------------------------------------------

``$ http POST http://localhost:24817/pulp/api/v3/distributions/ name='supermarket' base_path='supermarket' publication=$PUBLICATION_HREF``

You can have a look at the published "universe" metadata now:

``$ http localhost:24816/pulp_cookbook/content/supermarket/universe``

In your ``Berksfile`` you can use the following ``source`` to access the
Supermarket snapshot:

.. code:: ruby

   source 'http://localhost:24816/pulp_cookbook/content/supermarket/'
