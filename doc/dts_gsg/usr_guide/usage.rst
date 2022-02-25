Usage
=====

Configuration
-------------

Configuring your own execution file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First of all, you must configure execution.cfg as below:

.. code-block:: console

   [Execution1]
   crbs=<CRB IP Address>
   drivername=vfio-pci
   build_type=meson
   rx_mode=avx512
   test_suites=
       hello_world,
   targets=
       x86_64-native-linuxapp-gcc
   parameters=nic_type=cfg:func=true

* crbs: IP address of the DUT. The detail information is defined in file $DTS_CFG_FOLDER/crbs.cfg.
* drivername: the driver devices used by DPDK bound to.
* build_type: the tool for building DPDK, it can be meson.
* rx_mode: vector instructions used in tests, it can be novector/sse/avx2/avx512. it is optional, if not set, dpdk uses avx2 by default.
* test_suites: test suites and cases that to be executed. use ``:`` to separate suite and it's cases and use ``\`` to separate different cases.
* targets: DPDK targets to be tested.
* parameters: multiple keywords as following:

  * nic_type: it is the type of the NIC to use. The types are defined in the file settings.py.
    There's a special type named as **cfg**, which mean network information will be loaded from file $DTS_CFG_FOLDER/ports.cfg.
    If use NIC type such as niantic, fortville_25g, it requires all DUT are the same types and no any same devices connected to Tester,
    as DTS will test all devices connected to Tester. Therefore, recommend using **cfg**.
  * func=true: run only functional test.
  * perf=true: run only performance test.

.. note::

   The two options ``func=true`` and ``perf=true`` are mutually exclusive, as the traffic generators for functional and performance are mutually exclusive.

Here are an example for functional testing:

.. code-block:: console

   [Execution1]
   crbs=192.168.1.1
   drivername=vfio-pci
   build_type=meson
   test_suites=
        unit_tests_eal:test_version\test_common,
   targets=
        x86_64-default-linuxapp-gcc,
   parameters=nic_type=cfg:func=true


Configure CRB information
~~~~~~~~~~~~~~~~~~~~~~~~~

Then please add the detail information about your CRB in $DTS_CFG_FOLDER/crbs.conf as following:

.. code-block:: console

   [DUT IP]
   dut_ip=xxx.xxx.xxx.xxx
   dut_user=root
   dut_passwd=
   os=linux
   dut_arch=
   tester_ip=xxx.xxx.xxx.xxx
   tester_passwd=
   pktgen_group=
   channels=4
   bypass_core0=True
   dut_cores=

* DUT IP: section name, same as ``crbs`` in execution.cfg.
* dut_ip: IP address of the DUT, same as ``crbs`` in execution.cfg.
* dut_user: User name of DUT linux account
* dut_passwd: Password of DUT linux account
* tester_ip: IP address of tester
* tester_passwd: Password of Tester linux account, user name should same as dut_user
* pktgen_group: traffic generator name, it can be ``trex`` or ``ixia``, it is optional, if not set, DTS can't do performance tests.
* channels: number of memory channels for DPDK EAL
* bypass_core0: skip the first core when initialize DPDK
* dut_cores: DUT core list, eg: 1,2,3,4,5,18-22, it is optional, if it is ``None`` or not set, all core list will be used.

Here are an example for functional testing:

.. code-block:: console

   [192.168.1.1]
   dut_ip=192.168.1.1
   dut_user=root
   dut_passwd=dutpasswd
   os=linux
   tester_ip=192.168.1.2
   tester_passwd=testerpasswd
   channels=4
   bypass_core0=True


Configure port information
~~~~~~~~~~~~~~~~~~~~~~~~~~

If set ``nic_type=cfg`` in execution.cfg, please add port configuration in $DTS_CFG_FOLDER/ports.cfg as following:

.. code-block:: console

   [DUT IP]
   ports =
       pci=<Pci BDF>,peer=<Pci BDF>;
       pci=<Pci BDF>,peer=IXIA:X.Y;
       pci=<Pci BDF>,peer=TREX:X;

It supports three patterns, the first one is for functional testing, the second one is for ``IXIA``, the third one is for ``TRex``:

* pci: Device pci address of DUT
* peer: info of Tester port which connected to the DUT device:

  * if it is func testing, it is pci address
  * if pktgen is ``TRex``, the `X` in ``TREX:X`` is port id in TRex configuration file, e.g. /etc/trex_cfg.yaml.
  * if pktgen is ``IXIA``, the `X` is card id ,and the `Y` is port id, which configured in DTS_CFG_FOLDER/pktgen.cfg (./conf/pktgen.cfg by default).

Here are an example for functional testing:

.. code-block:: console

   [192.168.1.1]
   ports =
       pci=0000:06:00.0,peer=0000:81:00.0;
       pci=0000:06:00.1,peer=0000:81:00.1;

Here are an example for IXIA:

.. code-block:: console

   [192.168.1.1]
   ports =
       pci=0000:18:00.0,peer=IXIA:1.1;
       pci=0000:18:00.1,peer=IXIA:1.2;

Here are an example for TRex:

.. code-block:: console

   [192.168.1.1]
   ports =
       pci=0000:18:00.0,peer=TREX:1;
       pci=0000:18:00.1,peer=TREX:1;


Configure all test suites
~~~~~~~~~~~~~~~~~~~~~~~~~

$DTS_CFG_FOLDER/global_suite.cfg is a global suite configure file which is shared by all suites.

.. code-block:: console

    [global]
    vf_driver=vfio-pci

* vf_driver: VF driver that for VF testing, recommend keep the default value ``vfio-pci``.


Configure your own suites
~~~~~~~~~~~~~~~~~~~~~~~~~

Not all test suites have it's own configuration file which depended on script. If it has, the configuration file is $DTS_CFG_FOLDER/[suite_name].cfg
For example, suite metrics has its suite configure file $DTS_CFG_FOLDER/metric.cfg:

.. code-block:: console

    [suite]
    frames_cfg = { 64: 0.07, 128: 0.04, 256: 0.02, 512: 0.01, 1024: 0.01 }
    duration = 60
    sample_number = 3
    rates = [100, 80, 40, 20]


Configure your pktgen
~~~~~~~~~~~~~~~~~~~~~

Pktgen information are configured in $DTS_CFG_FOLDER/pktgen.cfg, pktgen_group must be configured too:

* traffic generator is ``TRex``, set ``pktgen_group=trex`` in crbs.cfg.
* traffic generator is ``IXIA``, set ``pktgen_group=ixia`` in crbs.cfg.

Then configure $DTS_CFG_FOLDER/pktgen.cfg as following:

.. code-block:: console

   [TREX]
   trex_root_path=/opt/trex/v2.84/
   trex_lib_path=/opt/trex/v2.84/automation/trex_control_plane/interactive
   config_file=/etc/trex_cfg.yaml
   server=192.168.1.1 # equal to tester IP, TREX should be installed in tester
   pcap_file=/opt/trex/v2.84/stl/sample.pacp
   core_num=16
   ip_src=16.0.0.1
   ip_dst=10.0.0.1
   warmup=15
   duration=-1
   start_trex=yes

   [IXIA]
   ixia_version=6.62
   ixia_ip=xxx.xxx.xxx.xxx
   ixia_ports=
       card=1,port=1;
       card=1,port=2;
       card=1,port=3;
       card=1,port=4;

* TREX: section name for TRex.
* trex_root_path: source code path for TRex
* trex_lib_path: the director where dts can import Trex API
* start_trex: whether DTS start TRex server, suggest 'yes' for one-time test, and 'no' for CI integration

* IXIA: section name for IXIA.
* ixia_version: the version of IxExplorer.
* ixia_ip: IP of ixia
* ixia_ports: ixia ports connected to DUT.

Here are an example for TRex:

.. code-block:: console

   [TREX]
   trex_root_path=/opt/trex/v2.84/
   trex_lib_path=/opt/trex/v2.84/automation/trex_control_plane/interactive
   config_file=/etc/trex_cfg.yaml
   server=192.168.1.1 # equal to tester IP, TREX should be installed in tester
   pcap_file=/opt/trex/v2.84/stl/sample.pacp
   core_num=16
   ip_src=16.0.0.1
   ip_dst=10.0.0.1
   warmup=15
   duration=-1
   start_trex=yes

Here are an example for IXIA:

.. code-block:: console

   [IXIA]
   ixia_version=9.00
   ixia_ip=192.168.2.1
   ixia_ports=
       card=3,port=1;
       card=3,port=2;
   ixia_force100g=disable


Running the Application
-----------------------

DTS supports multiple parameters which will select different of working mode of test framework.
In the meantime, DTS can work with none parameter, then every parameter will set to its default value:

.. code-block:: console

   usage: main.py [-h] [--config-file CONFIG_FILE] [--snapshot SNAPSHOT] [--output OUTPUT] [-s]
                  [-t TEST_CASES] [-d DIR] [-v] [--debug] [--debugcase] [--re_run RE_RUN]
                  [--commands COMMANDS] [--update-expected]

DTS supports the following parameters:

*   ``-h, --help``

    Display a help message and quit.

*   ``--config-file CONFIG_FILE``

    Execution file which contains test suites, DPDK target information and so on.
    The default value is `execution.cfg`.

*   ``--snapshot SNAPSHOT``

    Snapshot .tgz file to use as input。
    The deault value is `./dep/dpdk.tar.gz`.

*   ``--output OUTPUT``

    Output directory where dts log and result saved.
    The default value is `./output`.

*   ``-s, --skip-setup``

    Skip all possible setup steps done on both DUT and tester.

*   ``-t TEST_CASES, --test-cases TEST_CASES``

    Execute only the specific test cases.
    The default value is all test cases.

*   ``-d DIR``

    Output directory where dpdk package is extracted.

*   ``-v, --verbose``

    Enable verbose output, all message output on screen.

*   ``--debug``

    Enable debug mode, user can enter debug mode in process with `ctrl+c`
    User can do further debug by attached to sessions or call pdb module by interact interface:

.. code-block:: console

   help(): show help message
   list(): list all connected sessions
   connect(name): connect to session directly
   exit(): exit dts
   quit(): quit debug mode and into normal mode
   debug(): call python debug module

*   ``--debugcase``

   Enable debug mode with test cases.
   DTS will hang and wait for user command before executing each test case:

.. code-block:: console

   rerun(): rerun current case
   ctrl + d: exit current case

*   ``--re_run RE_RUN``

    Times that will re-run when case failed.
    The default value is 0, and it must be >=0.

*   ``--update-expected``

    Enable write-back expected value of performance.
    It requires test scripts support.

Here are examples:

.. code-block:: console

   ./dts
   ./dts -s
   ./dts -s -d /home/dpdk
   ./dts --debug
   ./dts --debug --debugcase
   ./dts --output test1
