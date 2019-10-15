=======================
pulp-cookbook Changelog
=======================

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see CONTRIBUTING.rst.

.. towncrier release notes start

0.1.0b3 (2019-10-15)
====================


Deprecations and Removals
-------------------------

- Change `_id`, `_created`, `_last_updated`, `_href` to `pulp_id`, `pulp_created`, `pulp_last_updated`, `pulp_href`. Remove `_type` field from content serializer.
  `#56 <https://github.com/gmbnomis/pulp_cookbook/issues/56>`_
- Remove "_" from `_versions_href`, `_latest_version_href`
  `#58 <https://github.com/gmbnomis/pulp_cookbook/issues/58>`_


----


0.1.0b2 (2019-10-04)
====================


Features
--------

- Use the new SingleArtifactContentUploadSerializer to implement the content upload function (single shot upload).
  `#18 <https://github.com/gmbnomis/pulp_cookbook/issues/18>`_


Deprecations and Removals
-------------------------

- Change `_artifact` field to `artifact` for cookbook content.
  `#46 <https://github.com/gmbnomis/pulp_cookbook/issues/46>`_


Misc
----

- `#48 <https://github.com/gmbnomis/pulp_cookbook/issues/48>`_


----


0.1.0b1 (2019-09-21)
====================


Features
--------

- - Migrations are checked in now.
  `#39 <https://github.com/gmbnomis/pulp_cookbook/issues/39>`_


Bugfixes
--------

- - Fix breaking changes introduced by DRF 3.10
  `#36 <https://github.com/gmbnomis/pulp_cookbook/issues/36>`_


----


Version 0.0.4b3
===============

Released on May 20, 2019

- Removed the publisher, publications can be created directly
- Fix: distributions now return the correct ``base_url``
- Adapt to pulpcore-plugin 0.1rc2

Version 0.0.4b2
===============

Released on Mar 31, 2019

- Adapt to pulpcore-plugin 0.1rc1

Version 0.0.4b1
===============

Released on Feb 5, 2019

- Support 'lazy' remote policies ('on_demand', 'streaming')
- live universe API migrated to new content app
- Implements "repo isolation". Content is shared between repos only if a
  cryptographic digest is known and is the same.
- Publish: Use repo key to check whether a repo version can be published without
  conflict.
- Adapt to pulpcore-plugin 0.1.0b18


Version 0.0.3a2
===============

Released on Dec 21, 2018

- Adapt to pulpcore-plugin 0.1.0b16


Version 0.0.3a1
===============

Released on Dec 19, 2018

- Adapt to pulpcore-plugin 0.1.0b15


Version 0.0.2a2
===============

Released on Sep 14, 2018

- Initial version with sync and publish support (suitable for berkshelf).

