=======================
pulp-cookbook Changelog
=======================

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see CONTRIBUTING.rst.

.. towncrier release notes start


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

