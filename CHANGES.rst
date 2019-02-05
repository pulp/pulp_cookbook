pulp-cookbook Changelog
=======================

Version 0.0.4b1
---------------

Released on Feb 5, 2019

- Support 'lazy' remote policies ('on_demand', 'streaming')
- live universe API migrated to new content app
- Implements "repo isolation". Content is shared between repos only if a
  cryptographic digest is known and is the same.
- Publish: Use repo key to check whether a repo version can be published without
  conflict.
- Adapt to pulpcore-plugin 0.1.0b18


Version 0.0.3a2
---------------

Released on Dec 21, 2018

- Adapt to pulpcore-plugin 0.1.0b16


Version 0.0.3a1
---------------

Released on Dec 19, 2018

- Adapt to pulpcore-plugin 0.1.0b15


Version 0.0.2a2
---------------

Released on Sep 14, 2018

- Initial version with sync and publish support (suitable for berkshelf).

