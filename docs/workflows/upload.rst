.. _workflows-upload:

Upload and Manage Content
=========================

The section shows how to upload content to Pulp.

Bear in mind that the attached snippets utilize ``pulp_http``. Refer to
:ref:`workflows-index` to learn more about these utilities and the required
tools (``httpie`` and ``jq``).

Create a repository
-------------------

If you don't already have a repository called ``foo``, create one:

.. literalinclude:: ../_scripts/create_repo_foo.sh
   :language: bash

Response:

.. literalinclude:: ../_snippets/create_repo_foo.txt
   :language: json


Upload local cookbooks to Pulp
------------------------------

As a simple example, let's download two cookbooks from the Chef Supermarket and
upload them into our ``foo`` repository.

Download 'ubuntu' and 'apt' cookbooks into the current directory (the 'ubuntu'
cookbooks depends on the 'apt' cookbook):

.. code-block:: bash

    curl -Lo ubuntu-2.0.1.tgz https://supermarket.chef.io:443/api/v1/cookbooks/ubuntu/versions/2.0.1/download``
    curl -Lo apt-7.0.0.tgz https://supermarket.chef.io:443/api/v1/cookbooks/apt/versions/7.0.0/download``

Now, we create a cookbook content unit (which represent a cookbook in Pulp) for
each file, respectively:

.. literalinclude:: ../_scripts/create_content_ubuntu.sh
   :language: bash

Response (finished task status):

.. literalinclude:: ../_snippets/create_content_ubuntu.txt
   :language: json

And for the apt cookbook:

.. literalinclude:: ../_scripts/create_content_apt.sh
   :language: bash

Response (finished task status):

.. literalinclude:: ../_snippets/create_content_apt.txt
   :language: json

Add content to repository ``foo``
---------------------------------

Once we have content unit(s), they can be added and removed and from to
repositories, creating a new repository version (which will be the latest
version):

.. literalinclude:: ../_scripts/add_content_to_repo.sh
   :language: bash


Response (finished task status):

.. literalinclude:: ../_snippets/add_content_to_repo.txt
   :language: json


One Shot upload
---------------

TODO
