.. SPDX-License-Identifier: BSD-3-Clause
   Copyright (c) <2022>, Intel Corporation

===========
Meson tests
===========

Description
===========
This test plan describes how to run unit tests with meson.
Test tests have been classified into five different groups.

- Fast tests.
- Performance tests.
- Driver tests.
- Extra tests.
- Debug tests.

For more details, please refer to `Running DPDK Unit Tests with Meson <http://doc.dpdk.org/guides/prog_guide/meson_ut.html>`_.

Prerequisites
=============

Required Libraries
------------------
* crypto relative cases require dependencies `libIPSec_MB` and `libcrypto`::

     cryptodev_aesni_mb_autotest
     cryptodev_aesni_gcm_autotest
     cryptodev_null_autotest
     cryptodev_openssl_autotest
     cryptodev_openssl_asym_autotest
     cryptodev_qat_autotest
     cryptodev_sw_kasumi_autotest
     cryptodev_sw_snow3g_autotest
     cryptodev_sw_zuc_autotest
     cryptodev_scheduler_autotest

  .. note::

     For more details, please refer to `Crypto Device Drivers <http://doc.dpdk.org/guides/cryptodevs/index.html>`_

* The following cases require dependencies `libpcap`::

   bpf_convert_autotest
   eal_flags_mem_autotest
   flow_classify_autotest
   efd_autotest
   efd_perf_autotest

General set up
--------------

* Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110

* Load rte_kni driver::

    # lsmod | grep rte_kni
    # rmmod rte_kni.ko
    # insmod ./<dpdk build dir>/kmod/rte_kni.ko lo_mode=lo_mode_fifo

   .. note::

      Test case fast-tests/kni_autotest requires to load kni.ko.

* Get the pci device id and interface of DUT and tester.
   For example, 0000:18:00.0 and 0000:18:00.1 is pci device id,
   ens785f0 and ens785f1 is interface::

    <dpdk dir># ./usertools/dpdk-devbind.py -s
	...
    0000:18:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci
    0000:18:00.1 'Device 159b' if=ens785f1 drv=ice unused=vfio-pci

* Bind the DUT port to dpdk::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:00.0 0000:18:00.1

.. note::

   kni_autotest requires at least one ethernet port, but other can be none.

Test case
=========

Test case 1: test_fasts
-------------------------------
This section explains how to run the meson tests for fast-tests.

test steps
~~~~~~~~~~
1. Run test on DUT::

    meson test -C x86_64-native-linuxapp-gcc --suite DPDK:fast-tests -t 1 --test-args="-c 0xff"

   * `-t` is used to specify the timeout of test case, unit is second.
   * `--test-args option` is used to specify test specific parameters,
     distributor_autotest and distributor_perf_autotest require core number less than 64.

2. Open and view the results on DUT::

    <dpdk dir># cat ./x86_64-native-linuxapp-gcc/meson-logs/testlog.txt

3. Check the result output log. All case results are "OK", for example::

    1/99 DPDK:fast-tests / acl_autotest                   OK              3.43s
    2/99 DPDK:fast-tests / atomic_autotest                OK              6.21s
    3/99 DPDK:fast-tests / bitmap_autotest                OK              1.18s
    4/99 DPDK:fast-tests / bpf_autotest                   OK              1.17s
    5/99 DPDK:fast-tests / bpf_convert_autotest           OK              1.19s

Test case 2: test_driver
-------------------------------
This section explains how to run the meson tests for driver-tests.

test steps
~~~~~~~~~~
1. Run test on DUT::

    meson test -C x86_64-native-linuxapp-gcc --suite DPDK:driver-tests -t 1 --test-args="-c 0xff"

2. Following test case 1 step 2 and step 3.

Test case 3: test_debug
-------------------------------
This section explains how to run the meson tests for debug-tests.

test steps
~~~~~~~~~~
1. Run test on DUT::

    meson test -C x86_64-native-linuxapp-gcc --suite DPDK:debug-tests -t 1 --test-args="-c 0xff"

2.Following test case 1 step 2 and step 3.

.. warning::

   `The bug <https://bugs.dpdk.org/show_bug.cgi?id=1002>_` impacts the following cases::

      DPDK:debug-tests/dump_struct_sizes
      DPDK:debug-tests/dump_mempool
      DPDK:debug-tests/dump_malloc_stats
      DPDK:debug-tests/dump_devargs
      DPDK:debug-tests/dump_log_types
      DPDK:debug-tests/dump_ring
      DPDK:debug-tests/dump_physmem
      DPDK:debug-tests/dump_memzone

Test case 4: test_extra
-------------------------------
This section explains how to run the meson tests for extra-tests.

test steps
~~~~~~~~~~
1. Run test on DUT::

    meson test -C x86_64-native-linuxapp-gcc --suite DPDK:extra-tests -t 1 --test-args="-c 0xff"

2. Following test case 1 step 2 and step 3.

.. warning::

   Extra-tests are know issues which are recorded in app/test/meson.build::

    #Tests known to have issues or which don't belong in other tests lists.
    extra_test_names = [
            'alarm_autotest', # ee00af60170b ("test: remove strict timing requirements some tests")
            'cycles_autotest', # ee00af60170b ("test: remove strict timing requirements some tests")
            'delay_us_sleep_autotest', # ee00af60170b ("test: remove strict timing requirements some tests")
            'red_autotest', # https://bugs.dpdk.org/show_bug.cgi?id=826]

Test case 5: test_perf
-------------------------------
This section explains how to run the meson tests for perf-tests.

test steps
~~~~~~~~~~
1. Run test on DUT::

    meson test -C x86_64-native-linuxapp-gcc --suite DPDK:perf-tests -t 1 --test-args="-c 0xff"

2. Following test case 1 step 2 and step 3.