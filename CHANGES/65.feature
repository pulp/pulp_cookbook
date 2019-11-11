Make repositories "typed". Repositories now live at a detail endpoint, i.e.
``/pulp/api/v3/repositories/cookbook/cookbook/``. Sync is performed by POSTing
to ``{repo_href}/sync/ remote={remote_href}`` instead of POSTing to the
``{remote_href}/sync/ repository={repo_href}`` endpoint. Creating a new
repository version (adding & removing content) is performed by POSTing to
``{repo_href}/modify/``
