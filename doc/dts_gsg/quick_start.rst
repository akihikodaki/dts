=================
Quick start guide
=================

Introduction
============

This document describes how to install and configure the Data Plane Development Kit Test Suite (DTS) in a Linux environment.
It is designed to get user to set up DTS quickly in their environment without going deeply into detail.

DTS can run on a tester machine or a DUT machine or the third machine to communicate/manage tester/DUT by SSH connection.
DTS supports different kinds of traffic generators, including Scapy, TRex, IXIA.
The example set up DTS on as tester machine, and use Scapy as traffic generator to run functional testing.

System Requirements
===================

This chapter describes the packages required to set up DTS.
For the DPDK requirements, please consult `Data Plane Development Kit Getting Started Guide <http://dpdk.org/doc/guides>`_.

Hardware Recommendation
-----------------------

Our regression setups uses Intel x86 platforms with mainstream Intel ethernet cards.
The following platforms have been tested and are recommended.

.. |reg|    unicode:: U+000AE .. REGISTERED SIGN
.. |trade|    unicode:: U+2122 .. TRADE MARK SIGN

* DTS and Tester system

	* CPU
		* Intel\ |reg| Xeon\ |reg| Platinum 8280M CPU @ 2.70GHz
		* Intel\ |reg| Xeon\ |reg| Platinum 8180 CPU @ 2.50GHz
		* Intel\ |reg| Xeon\ |reg| Gold 6252N CPU @ 2.30GHz

	* OS
		* Ubuntu 20.04
		* Ubuntu 18.04

* DUT system

	* CPU

		* Intel\ |reg| Atom\ |trade| CPU C3758 @ 2.20GHz
		* Intel\ |reg| Atom\ |trade| CPU C3858 @ 2.00GHz
		* Intel\ |reg| Atom\ |trade| CPU C3958 @ 2.00GHz
		* Intel\ |reg| Xeon\ |reg| CPU D-1541 @ 2.10GHz
		* Intel\ |reg| Xeon\ |reg| CPU D-1553N @ 2.30GHz
		* Intel\ |reg| Xeon\ |reg| CPU E5-2680 0 @ 2.70GHz
		* Intel\ |reg| Xeon\ |reg| CPU E5-2680 v2 @ 2.80GHz
		* Intel\ |reg| Xeon\ |reg| CPU E5-2699 v3 @ 2.30GHz
		* Intel\ |reg| Xeon\ |reg| CPU E5-2699 v4 @ 2.20GHz
		* Intel\ |reg| Xeon\ |reg| Gold 5218N CPU @ 2.30GHz
		* Intel\ |reg| Xeon\ |reg| Gold 6139 CPU @ 2.30GHz
		* Intel\ |reg| Xeon\ |reg| Gold 6252N CPU @ 2.30GHz
		* Intel\ |reg| Xeon\ |reg| Platinum 8180 CPU @ 2.50GHz
		* Intel\ |reg| Xeon\ |reg| Platinum 8280M CPU @ 2.70GHz

	* OS

		* CentOS 8.3
		* CentOS Stream 8
		* Fedora 33
		* Red Hat Enterprise Linux Server release 8.3
		* Suse 15 SP2
		* Ubuntu 20.04
		* Ubuntu 20.10

	* NICs

	        * Intel\ |reg| Ethernet Controller E810-C for SFP (4x25G)
	        * Intel\ |reg| Ethernet Controller E810-C for QSFP (2x100G)
	        * Intel\ |reg| Ethernet Converged Network Adapter X710-DA4 (4x10G)
	        * Intel\ |reg| Ethernet Converged Network Adapter XXV710-DA2 (2x25G)
	        * Intel\ |reg| 82599ES 10 Gigabit Ethernet Controller

Topology Example
----------------

2 Teseter interfaces connect to 2 DUT interfaces back to back.

Dependencies
------------

SSH Service
~~~~~~~~~~~

Tester and DUT should have one interface connected to the same internet, so that they can be accessed by each other from local IP address

.. code-block:: console

   apt-get install sshd                # download / install ssh software
   systemctl enable ssh                # start ssh service

.. note::

   Firewall should be disabled that all packets can be accepted by NIC interfaces.

.. code-block:: console

   systemctl disable firewalld.service

Python modules for DTS & Tester
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The python dependences are recorded in requirements.txt.
Please install them as the following:

.. code-block:: console

   apt-get install python3
   python3 -m pip install requirements.txt

BIOS setting for DUT
~~~~~~~~~~~~~~~~~~~~

DPDK prefer devices bound to ``vfio-pci`` kernel module, therefore, please enable VT-d and VT-x:

.. code-block:: console

   Advanced -> Integrated IO Configuration -> Intel(R) VT for Directed I/O <Enabled>
   Advanced -> Processor Configuration -> Intel(R) Virtualization Technology <Enabled>

DPDK running Prerequisite
~~~~~~~~~~~~~~~~~~~~~~~~~

Recommend to use 1G Hugepage for DPDK running, add ``hugepagesz=1G hugepages=40 default_hugepagesz=1G`` in Linux cmdline.
For more details, please refer to `Data Plane Development Kit Getting Started Guide <http://dpdk.org/doc/guides>`_.

Running DTS
===========

Getting DTS Code
----------------

Get DTS code from remote repo.

.. code-block:: console

   [root@tester ~]#  git clone http://dpdk.org/git/tools/dts
   [root@tester ~]#  ls dts
   [root@tester dts]# conf CONTRIBUTING.TXT dep doc dts execution.cfg executions framework nics output requirements.txt test_plans tests tools version.py

Preparing DPDK tarball
----------------------

DPDK source code should be packed as "dpdk.tar.gz" and moved into dts/dep:

.. code-block:: console

    tar -czvf dpdk.tar.gz dpdk
    cp dpdk.tar.gz ~/dts/dep

Configuring DTS
---------------

A few of files should be configured, including execution.cfg, conf/crbs, conf/ports.cfg.

execution.cfg
~~~~~~~~~~~~~

.. code-block:: console

   [Execution1]
   crbs=192.168.1.1
   drivername=vfio-pci
   build_type=meson
   test_suites=
        hello_world,
   targets=
        x86_64-default-linuxapp-gcc,
   parameters=nic_type=cfg:func=true

* crbs: IP address of the DUT system
* test_suites: a list of test suites to be executed

conf/crbs.cfg
~~~~~~~~~~~~~

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

* dut_ip: IP address of the DUT system, same as crbs in execution.cfg
* dut_user: User name of DUT linux account
* dut_passwd: Password of DUT linux account
* tester_ip: IP address of tester
* tester_passwd: Password of Tester linux account, user name should same as dut_user

conf/ports.cfg
~~~~~~~~~~~~~~

.. code-block:: console

   [192.168.1.1]
   ports =
       pci=0000:06:00.0,peer=0000:81:00.0;
       pci=0000:06:00.1,peer=0000:81:00.1;

* [192.168.1.1]: same as crbs in execution.cfg and dut_ip in conf/crbs.cfg
* pci: pci address of DUT port
* peer: pci address of Tester port which connected to the DUT port whose pci is `pci`.

The topology for the configuration is:

.. code-block:: console

   DUT port0 (0000:06:00.0) --- Tester port0 (0000:81:00.0)
   DUT port0 (0000:06:00.1) --- Tester port0 (0000:81:00.1)

Launch DTS
----------

As we have prepared the zipped dpdk file and configuration file, just type the followed command “./dts”, it will start the validation process.

.. code-block:: console

    [root@tester ~]# ./dts

                           dts:
    DUT 192.168.1.1
                        tester: ssh root@192.168.1.2
                        tester: ssh root@192.168.1.2
                        tester: python3 -V
                  tester_scapy: ssh root@192.168.1.2
                  ...
             dut.192.168.1.1: ssh root@192.168.1.1
             dut.192.168.1.1: ssh root@192.168.1.1
             ...
             dut.192.168.1.1: scp -v dep/dpdk.tar.gz root@192.168.1.1:/tmp/
             ...
             dut.192.168.1.1: DUT PORT MAP: [0, 1]
             ...
             dut.192.168.1.1: export RTE_TARGET=x86_64-native-linuxapp-gcc
             dut.192.168.1.1: export RTE_SDK=`pwd`
             dut.192.168.1.1: rm -rf x86_64-native-linuxapp-gcc
             dut.192.168.1.1: CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static x86_64-native-linuxapp-gcc
             ...
             dut.192.168.1.1: usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:af:00.0 0000:af:00.1
                        dts: NIC :        fortville_25g
             dut.192.168.1.1: meson configure -Dexamples=helloworld x86_64-native-linuxapp-gcc
             dut.192.168.1.1: ninja -C x86_64-native-linuxapp-gcc
             dut.192.168.1.1: ls x86_64-native-linuxapp-gcc/examples/dpdk-helloworld
                TestHelloWorld: Test Case test_hello_world_all_cores Begin
             dut.192.168.1.1: cat config/defconfig_x86_64-native-linuxapp-gcc | sed '/^#/d' | sed '/^\s*$/d'
             dut.192.168.1.1: ./x86_64-native-linuxapp-gcc/examples/dpdk-helloworld  -l 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71 -n 4   --file-prefix=dpdk_25703_20210311003827
                TestHelloWorld: Test Case test_hello_world_all_cores Result PASSED:
                TestHelloWorld: Test Case test_hello_world_single_core Begin
             dut.192.168.1.1: ./x86_64-native-linuxapp-gcc/examples/dpdk-helloworld  -l 1 -n 4   --file-prefix=dpdk_25703_20210311003827
                TestHelloWorld: Test Case test_hello_world_single_core Result PASSED:
                           dts:
    TEST SUITE ENDED: TestHelloWorld
             ...
             dts: DTS ended
    [root@tester ~]#

Check Test Result
==================

The result files are generated in dts/output.

.. code-block:: console

   [root@tester output]# ls
   rst_report  dts.log  statistics.txt  TestHelloWorld.log  test_results.json  test_results.xls

*   statstics.txt: summary statistics

.. code-block:: console

   [root@tester output]# cat statistics.txt
   dpdk_version = 21.02.0
   Passed     = 2
   Failed     = 0
   Blocked    = 0
   Pass rate  = 100.0

*   test_result.json: json format result file

.. code-block:: console

   [root@tester output]# cat result.json
    {
        "192.168.1.1": {
            "dpdk_version": "21.02.0",
            "nic": {
                "driver": "vfio-pci",
                "firmware": "8.00 0x80008c1a 1.2766.0",
                "kdriver": "i40e-2.13.10",
                "name": "fortville_25g"
            },
            "x86_64-native-linuxapp-gcc": {
                "hello_world/test_hello_world_all_core": "passed"
                "hello_world/test_hello_world_single_core": "passed"
            }
        }
    }

*   test_result.xls: excel format result file

.. figure:: image/dts_result.png
