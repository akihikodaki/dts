Tutorial
========

Functional Test Tutorial
------------------------
Tutorial of functional test.

Execution configuration
~~~~~~~~~~~~~~~~~~~~~~~
By default, DTS will load execution tasks from execution.cfg. In this file, user can assign multiple tasks to DTS. For each task, DTS will initialize dpdk environment on DUT and run test suites listed. As example below, user assigned one execution task on 127.0.0.1.

Details of the task is defined by some settings like target, NIC type, functional or performance case and foremost the list of suites which will be executed.

.. code-block:: console

   [127.0.0.1]
   crbs=127.0.0.1
   drivername=igb_uio
   test_suites=
       vlan
   targets=
   x86_64-native-linuxapp-gcc
   parameters=nic_type=cfg:func=true

DUT&Tester configuration
~~~~~~~~~~~~~~~~~~~~~~~~
In previous chapter, we assume that user has assigned some execution task on 127.0.0.1. DTS will create the SSH connections to the DUT and tester which connected to it in the runtime. After session established, DTS will setup kernel modules and hugepages on DUT. The procedures for different OS maybe different, so type of OS is also needed to be configured by manual.

.. code-block:: console

   cat ./conf/crbs.cfg
   [127.0.0.1]
   dut_ip=127.0.0.1
   dut_user=root
   dut_passwd=xxx
   os=linux
   tester_ip=192.168.1.1
   tester_passwd=xxx
   ixia_group=None
   channels=4
   bypass_core0=True

Network topology configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
By default DTS will detect network topology automatically, but in certain occasions it can’t be done like no kernel module available for latest NIC or tester’s port need special settings. For resolving those kind of problems, DTS also support manually specify ports connections. The concept is that user only need to specify PCI devices under test and peer PCI address on tester server. In below sample, we defined network topology that DUT pci device (18:00.0) connected to pci device (1b:00.0) on 192.168.1.1. 

.. code-block:: console

   cat ./conf/ports.cfg
   [127.0.0.1]
   ports =
       pci=0000:18:00.0,peer=0000:1b:00.0;

Running execution
~~~~~~~~~~~~~~~~~
Before running real task, DPDK release packet should be saved under dep folder. 
Make sure that files will be extracted to folder name same as default output directory (dpdk).

.. code-block:: console

   cp dpdk.tar.gz dep/
   ./dts


Performance Test Tutorial
-------------------------
Turtorial of performance test.

Execution configuration
~~~~~~~~~~~~~~~~~~~~~~~
Like functional test, performance execution need configure CRB, target, NIC type and suites. Only difference is that performance option should be true in parameters setting.

.. code-block:: console

   [127.0.0.1]
   crbs=127.0.0.1
   drivername=igb_uio
   test_suites=
       l2fwd
   targets=
       x86_64-native-linuxapp-gcc
   parameters=nic_type=cfg:perf=true

DUT&Tester configuration
~~~~~~~~~~~~~~~~~~~~~~~~
DTS now support two kinds of packet generators. One is hardware packet generator IXIA, the other is dpdk based packet generator. Here is the sample for IXIA, IXIA's hardware resource like ports will be managed by groups in DTS. User need to assign which group will be used, and therefore IXIA ports in the group will be extended to tester's ports list.

.. code-block:: console

   cat ./conf/crbs.cfg
   [127.0.0.1]
   dut_ip=127.0.0.1
   dut_user=root
   dut_passwd=xxx
   os=linux
   tester_ip=192.168.1.1
   tester_passwd=xxx
   ixia_group=IXIA
   channels=4
   bypass_core0=True

.. code-block:: console

   cat ./conf/ixia.cfg
   [IXIA]
   ixia_version=6.62
   ixia_ip=xxx.xxx.xxx.xxx
   ixia_ports=
       card=1,port=1;
       card=1,port=2;
   ixia_force100g=disable

When there's none IXIA group configured in CRB's cfg file, DTS will try to use dpdk based packet generator for alternative. Apparently dpdk based packet generator can't meet all the requirements like latency,RFC2544 and random packets. The statistics reported by dpdk pktgen were just for reference.

Dpdk based packet generator will request for dpdk running environment. So that user should prepare required kernel module igb_uio.ko under tester's root directory. Due to packet generator can't support one-time build and run on all platforms, user should also prepare pktgen binary under tester's root directory. By now supported combination is dpdk v18.02 + dpdk-pktgen v3.5.0. Download link: http://dpdk.org/browse/apps/pktgen-dpdk/

.. code-block:: console

   cat ./conf/crbs.cfg
   ...
   ixia_group=None
   ...

Network topology configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default network topology of IXIA ports can be detected automatically. DTS also support manually configure network topo.

.. code-block:: console

   cat ./conf/ports.cfg
   [127.0.0.1]
   ports =
       pci=0000:18:00.0,peer=IXIA:1.1;
       pci=0000:18:00.1,peer=IXIA:1.2;

Running execution
~~~~~~~~~~~~~~~~~
Same as functional test.
