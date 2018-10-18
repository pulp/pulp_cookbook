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
- In general, this plugin is at an early stage.

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

   pulp-manager makemigrations pulp_cookbook
   pulp-manager migrate pulp_cookbook

Run Services
------------

.. code-block:: bash

   pulp-manager runserver
   sudo systemctl restart pulp_resource_manager
   sudo systemctl restart pulp_worker@1
   sudo systemctl restart pulp_worker@2

Create a repository ``foo``
---------------------------

``$ http POST http://localhost:8000/pulp/api/v3/repositories/ name=foo``

.. code:: json

    {
        "_href": "/pulp/api/v3/repositories/1/",
        "_latest_version_href": null,
        "_versions_href": "/pulp/api/v3/repositories/1/versions/",
        "created": "2018-09-05T20:00:34.872345Z",
        "description": "",
        "id": 1,
        "name": "foo",
        "notes": {}
    }

``$ export REPO_HREF=$(http :8000/pulp/api/v3/repositories/ | jq -r '.results[] | select(.name == "foo") | ._href')``

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

    ubuntu_resp=$(http --form POST http://localhost:8000/pulp/api/v3/artifacts/ file@ubuntu-2.0.1.tgz)
    echo "$ubuntu_resp" | jq .
    export UBUNTU_ARTIFACT_HREF=$(echo "$ubuntu_resp" | jq -r '._href')


.. code:: json

    {
    "id": 1,
    "_href": "/pulp/api/v3/artifacts/1/",
    "created": "2018-09-05T20:00:37.719715Z",
    "file": "/var/lib/pulp/artifact/32/a7d3de4ff8f769eeab4ffc982eb8df845d91d49c01548d6f993b10e52b6f69",
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

    apt_resp=$(http --form POST http://localhost:8000/pulp/api/v3/artifacts/ file@apt-7.0.0.tgz)
    echo "$apt_resp" | jq .
    export APT_ARTIFACT_HREF=$(echo "$apt_resp" | jq -r '._href')

Create ``cookbook`` content from an Artifact
--------------------------------------------

Create a content unit for ubuntu 2.0.1:

``$ http POST http://localhost:8000/pulp/api/v3/content/cookbook/cookbooks/ name="ubuntu" artifact="$UBUNTU_ARTIFACT_HREF"``

.. code:: json

    {
        "_href": "/pulp/api/v3/content/cookbook/cookbooks/1/",
        "artifact": "/pulp/api/v3/artifacts/1/",
        "created": "2018-09-05T20:00:38.164310Z",
        "dependencies": {
            "apt": ">= 0.0.0"
        },
        "id": 1,
        "name": "ubuntu",
        "notes": {},
        "type": "cookbook",
        "version": "2.0.1"
    }

``$ export UBUNTU_CONTENT_HREF=$(http :8000/pulp/api/v3/content/cookbook/cookbooks/?name=ubuntu | jq -r '.results[0]._href')``

Create a content unit for apt 7.0.0:

``$ http POST http://localhost:8000/pulp/api/v3/content/cookbook/cookbooks/ name="apt" artifact="$APT_ARTIFACT_HREF"``

.. code:: json

    {
        "_href": "/pulp/api/v3/content/cookbook/cookbooks/2/",
        "artifact": "/pulp/api/v3/artifacts/2/",
        "created": "2018-09-05T20:00:40.897876Z",
        "dependencies": {},
        "id": 2,
        "name": "apt",
        "notes": {},
        "type": "cookbook",
        "version": "7.0.0"
    }

``$ export APT_CONTENT_HREF=$(http :8000/pulp/api/v3/content/cookbook/cookbooks/?name=apt | jq -r '.results[0]._href')``


Add content to repository ``foo``
---------------------------------

``$ http POST :8000$REPO_HREF'versions/' add_content_units:="[\"$UBUNTU_CONTENT_HREF\",\"$APT_CONTENT_HREF\"]"``


Create a ``cookbook`` Publisher
-------------------------------

``$ http POST http://localhost:8000/pulp/api/v3/publishers/cookbook/ name=publisher``


.. code:: json

    {
        "_href": "/pulp/api/v3/publishers/cookbook/1/",
        "created": "2018-09-05T20:00:42.277819Z",
        "distributions": [],
        "id": 1,
        "last_published": null,
        "last_updated": "2018-09-05T20:00:42.277843Z",
        "name": "publisher",
        "type": "cookbook"
    }

``$ export PUBLISHER_HREF=$(http :8000/pulp/api/v3/publishers/cookbook/ | jq -r '.results[] | select(.name == "publisher") | ._href')``


Use the ``publisher`` Publisher to create a Publication
-------------------------------------------------------

``$ http POST :8000$PUBLISHER_HREF'publish/' repository=$REPO_HREF``

.. code:: json

    {
        "task": "/pulp/api/v3/tasks/66da00ea-fdc9-43f1-a9ef-95180db278a9/"
    }

``$ export PUBLICATION_HREF=$(http :8000/pulp/api/v3/publications/ | jq -r --arg PUBLISHER_HREF "$PUBLISHER_HREF" '.results[] | select(.publisher==$PUBLISHER_HREF) | ._href')``


Create a Distribution at 'foo' for the Publication
--------------------------------------------------

``$ http POST http://localhost:8000/pulp/api/v3/distributions/ name='baz' base_path='foo' publication=$PUBLICATION_HREF``

.. code:: json

    {
        "_href": "/pulp/api/v3/distributions/1/",
        "base_path": "foo",
        "base_url": "localhost:8000/pulp/content/foo",
        "created": "2018-09-05T20:00:44.482852Z",
        "id": 1,
        "name": "baz",
        "publication": "/pulp/api/v3/publications/1/",
        "publisher": null,
        "repository": null
    }

You can have a look at the published "universe" metadata now:

``$ http http://localhost:8000/pulp_cookbook/market/foo/universe``

.. code:: json

    {
        "apt": {
            "7.0.0": {
                "dependencies": {},
                "download_url": "http://localhost:8000/pulp/content/foo/cookbook_files/apt/7_0_0/apt-7.0.0.tar.gz",
                "location_path": "http://localhost:8000/pulp/content/foo/cookbook_files/apt/7_0_0/apt-7.0.0.tar.gz",
                "location_type": "uri"
            }
        },
        "ubuntu": {
            "2.0.1": {
                "dependencies": {
                    "apt": ">= 0.0.0"
                },
                "download_url": "http://localhost:8000/pulp/content/foo/cookbook_files/ubuntu/2_0_1/ubuntu-2.0.1.tar.gz",
                "location_path": "http://localhost:8000/pulp/content/foo/cookbook_files/ubuntu/2_0_1/ubuntu-2.0.1.tar.gz",
                "location_type": "uri"
            }
        }
    }


Use Berkshelf with the published repo
-------------------------------------

Create a Berksfile with the following content:


.. code:: ruby

   source 'http://localhost:8000/pulp_cookbook/market/foo'

   cookbook 'ubuntu'


``$ berks install``

.. code:: ruby

   Resolving cookbook dependencies...
   Fetching cookbook index from http://localhost:8000/pulp_cookbook/market/foo...
   Installing apt (7.0.0) from http://localhost:8000/pulp_cookbook/market/foo ([uri] http://localhost:8000/pulp/content/foo/cookbook_files/apt/7_0_0/apt-7.0.0.tar.gz)
   Installing ubuntu (2.0.1) from http://localhost:8000/pulp_cookbook/market/foo ([uri] http://localhost:8000/pulp/content/foo/cookbook_files/ubuntu/2_0_1/ubuntu-2.0.1.tar.gz)


Create a new remote ``supermarket``
-----------------------------------

In addition to uploading content, ``pulp_cookbook`` allows to synchronize a repo
with an upstream repo (that has to provide a "universe" endpoint).

Let's mirror the ``pulp`` and ``qpid`` cookbooks into our existing repo. First, we have to create a remote:

``$ http POST http://localhost:8000/pulp/api/v3/remotes/cookbook/ name='supermarket' url='https://supermarket.chef.io/' cookbooks:='{"pulp": "", "qpid": ""}'``

.. code:: json

    {
        "_href": "/pulp/api/v3/remotes/cookbook/1/",
        "cookbooks": {
            "pulp": "",
            "qpid": ""
        },
        "created": "2018-09-05T20:23:09.750080Z",
        "id": 1,
        "last_synced": null,
        "last_updated": "2018-09-05T20:23:09.750113Z",
        "name": "supermarket",
        "proxy_url": "",
        "ssl_validation": true,
        "type": "cookbook",
        "url": "https://supermarket.chef.io/",
        "validate": true
    }

``$ export REMOTE_HREF=$(http :8000/pulp/api/v3/remotes/cookbook/ | jq -r '.results[] | select(.name == "supermarket") | ._href')``

Sync repository ``foo`` using remote ``supermarket``
----------------------------------------------------

We don't want to delete the ``apt`` and ``ubuntu`` coobooks previously imported.
Therefore, we sync in 'additive' mode by setting ``mirror`` to false.

``$ http POST :8000$REMOTE_HREF'sync/' repository=$REPO_HREF mirror:=false``

Look at the new Repository Version created
------------------------------------------

``$ http GET ':8000'$REPO_HREF'versions/2/'``

.. code:: json

    {
        "_added_href": "/pulp/api/v3/repositories/1/versions/2/added_content/",
        "_content_href": "/pulp/api/v3/repositories/1/versions/2/content/",
        "_href": "/pulp/api/v3/repositories/1/versions/2/",
        "_removed_href": "/pulp/api/v3/repositories/1/versions/2/removed_content/",
        "base_version": null,
        "content_summary": {
            "cookbook": 4
        },
        "created": "2018-09-05T20:34:22.636271Z",
        "id": 2,
        "number": 2
    }

At the time of writing, there was only a single version of the ``pulp`` and
``qpid`` cookbooks available, respectively. This brings the total count to 4 cookbooks.

Publish the newest version
--------------------------

To publish the version just created, do:

``$ http POST :8000$PUBLISHER_HREF'publish/' repository=$REPO_HREF``

And update the distribution:

``$ http PATCH :8000/pulp/api/v3/distributions/1/ publication=/pulp/api/v3/publications/2/``

Now, the universe endpoint
``http://localhost:8000/pulp_cookbook/market/foo/universe`` will show the
content of the new repo version.
