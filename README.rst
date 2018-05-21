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

- Syncing remote repositories (e.g. Chef Supermarket)
- Full support of the `Supermarket API <https://docs.chef.io/supermarket_api.html>`_
- This plugin is at a very early stage. It has no tests and error cases have not
  been tested.

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

Install ``pulp_cookbook`` from source
-------------------------------------

1)  ``sudo -u pulp -i``
2)  ``source ~/pulpvenv/bin/activate``
3)  ``git clone https://github.com/pulp/pulp_cookbook.git``
4)  ``cd pulp_cookbook``
5)  ``python setup.py develop``
6)  ``pulp-manager makemigrations pulp_cookbook``
7)  ``pulp-manager migrate pulp_cookbook``
8)  ``django-admin runserver``
9)  ``sudo systemctl restart pulp_resource_manager``
10) ``sudo systemctl restart pulp_worker@1``
11) ``sudo systemctl restart pulp_worker@2``

Create a repository ``foo``
---------------------------

``$ http POST http://localhost:8000/pulp/api/v3/repositories/ name=foo``

.. code:: json

    {
        "_href": "http://localhost:8000/pulp/api/v3/repositories/012ddb4b-2a5c-438b-8a2c-8e860fc7ff70/",
        "_latest_version_href": null,
        "_versions_href": "http://localhost:8000/pulp/api/v3/repositories/012ddb4b-2a5c-438b-8a2c-8e860fc7ff70/versions/",
        "created": "2018-05-10T15:09:25.598418Z",
        "description": "",
        "id": "012ddb4b-2a5c-438b-8a2c-8e860fc7ff70",
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
    "id": "df361637-d606-41db-b7dd-d8e773e8c0a2",
    "_href": "http://localhost:8000/pulp/api/v3/artifacts/df361637-d606-41db-b7dd-d8e773e8c0a2/",
    "created": "2018-05-10T15:09:28.041601Z",
    "file": "/var/lib/pulp/artifact/32/a7d3de4ff8f769eeab4ffc982eb8df845d91d49c01548d6f993b10e52b6f69",
    "size": 3712,
    ...
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
        "_href": "http://localhost:8000/pulp/api/v3/content/cookbook/cookbooks/9c20888c-6a34-40da-88f7-428c6f04f273/",
        "artifact": "http://localhost:8000/pulp/api/v3/artifacts/df361637-d606-41db-b7dd-d8e773e8c0a2/",
        "created": "2018-05-10T15:09:28.575190Z",
        "dependencies": {
            "apt": ">= 0.0.0"
        },
        "id": "9c20888c-6a34-40da-88f7-428c6f04f273",
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
        "_href": "http://localhost:8000/pulp/api/v3/content/cookbook/cookbooks/b3f28b18-9279-446f-8ddd-50a8e9f5fb1a/",
        "artifact": "http://localhost:8000/pulp/api/v3/artifacts/2ac8857f-93e0-48d8-9046-2ea0d53b9d30/",
        "created": "2018-05-10T15:09:31.563556Z",
        "dependencies": {},
        "id": "b3f28b18-9279-446f-8ddd-50a8e9f5fb1a",
        "name": "apt",
        "notes": {},
        "type": "cookbook",
        "version": "7.0.0"
    }

``$ export APT_CONTENT_HREF=$(http :8000/pulp/api/v3/content/cookbook/cookbooks/?name=apt | jq -r '.results[0]._href')``


Add content to repository ``foo``
---------------------------------

``$ http POST $REPO_HREF'versions/' add_content_units:="[\"$UBUNTU_CONTENT_HREF\",\"$APT_CONTENT_HREF\"]"``


Create a ``cookbook`` Publisher
-------------------------------

``$ http POST http://localhost:8000/pulp/api/v3/publishers/cookbook/ name=publisher``


.. code:: json

    {
        "_href": "http://localhost:8000/pulp/api/v3/publishers/cookbook/d51f31df-5758-47ba-95e2-016eae4bb611/",
        "created": "2018-05-10T15:09:33.191839Z",
        "distributions": [],
        "id": "d51f31df-5758-47ba-95e2-016eae4bb611",
        "last_published": null,
        "last_updated": "2018-05-10T15:09:33.191857Z",
        "name": "publisher",
        "type": "cookbook"
    }

``$ export PUBLISHER_HREF=$(http :8000/pulp/api/v3/publishers/cookbook/ | jq -r '.results[] | select(.name == "publisher") | ._href')``


Use the ``publisher`` Publisher to create a Publication
-------------------------------------------------------

``$ http POST $PUBLISHER_HREF'publish/' repository=$REPO_HREF``

.. code:: json

    {
        "_href": "http://localhost:8000/pulp/api/v3/tasks/66b80927-93a0-465d-a7fc-2d2922bca77f/",
        "task_id": "66b80927-93a0-465d-a7fc-2d2922bca77f"
    }

``$ export PUBLICATION_HREF=$(http :8000/pulp/api/v3/publications/ | jq -r --arg PUBLISHER_HREF "$PUBLISHER_HREF" '.results[] | select(.publisher==$PUBLISHER_HREF) | ._href')``

Create a Distribution at 'foo' for the Publication
--------------------------------------------------

``$ http POST http://localhost:8000/pulp/api/v3/distributions/ name='baz' base_path='foo' publication=$PUBLICATION_HREF``

.. code:: json

    {
        "_href": "http://localhost:8000/pulp/api/v3/distributions/92acec58-e579-4647-94e2-4801f5b71595/",
        "base_path": "foo",
        "base_url": "localhost:8000/pulp/content/foo",
        "created": "2018-05-10T15:09:35.390266Z",
        "id": "92acec58-e579-4647-94e2-4801f5b71595",
        "name": "baz",
        "publication": "http://localhost:8000/pulp/api/v3/publications/bf30ed42-719f-42ef-bd87-a8557d57584c/",
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

