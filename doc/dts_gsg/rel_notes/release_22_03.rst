.. SPDX-License-Identifier: BSD-3-Clause
   Copyright 2022 The DTS contributors

DTS Release 22.03
=================

New Features
------------

* **Add new test plans.**

* **Add new test suites.**


Removed Items
-------------

* **Remove test plans.**

* **Remove test suites.**


Removed Items
-------------

**Removed Makefile Builds.**

Support for makefile builds has been removed.


Deprecation Notices
-------------------

**Unit Testing**

DPDK provide 2 ways to run unit test, one is `dpdk-test` app, the other is `meson test` command.
Support for running unit tests through `dpdk-test` app is now deprecated and will be removed in the next release.
Instead `meson test` command will be executed.
