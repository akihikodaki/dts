System Requirements
===================

The board assigned to be tester should be installed the latest Fedora distribution for easily installed DPDK Test Suite required python modules. Tester board needs plug at least 2 x Intel® 82599 (Niantic) NICs (2x 10GbE full duplex optical ports per NIC) in the PCI express slots, then connect these four Niantic ports to the DUT board and make sure the link has been started up and speed is 10000Mb/s.

Beside the four Niantic ports, tester and DUT should also have one interface connected to the same intranet. So that they can be accessed by each other from local IP address.

.. note::

   Firewall should be disabled that all packets can be accepted by Niantic Interface.

.. code-block:: console

   systemctl disable firewalld.service

Setup Tester Environment
------------------------

.. note::

   Please install the latest ubuntu distribution on the tester before install DPDK Test Suite on tester. Currently we recommend ubuntu 18.04 for tester. The setup instruction and required packages may be different on different operation systems.

To enable tester environment, you need to install script language, tool chain and third party packet generator, etc.

Please follow the guidance to finish install as the below section.

SSH Service
~~~~~~~~~~~
Since DPDK Test Suite Tester communicates with DUT via SSH, please install and start sshd service in your tester.

.. code-block:: console

   apt-get install sshd                # download / install ssh software
   systemctl enable ssh                # start ssh service

For create authorized login session, user needs to generate RSA authentication keys to ssh connection.

Please use the following commands:

.. code-block:: console

   ssh-keygen -t rsa

TCL Language Support modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since some third party tools required TCL (Tool Command Language) supports, please install TCL package to control and connect third party package generator. (For example, third-party professional tester IXIA required TCL support)

.. code-block:: console

   apt-get install tcl                 # download / install tcl software

Install Third Party python modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With third party module, DPDK Test Suite is able to export test result as MS Excel file or graphs. To support this feature, please install the following modules in the tester.
Python Module “xlwt”: this module is used to generate spreadsheet files which compatible with MS Excel 97/2000/XP/2003 XLS files.
Python Module “numpy”: this module provides method to deal with array-processing test results.
Python Module “pexpect”: this module provides API to automate interactive SSH sessions.
Python Module “docutils”: Docutils is a modular system for processing documentation into useful formats, such as HTML, XML, and LaTeX.
Python Module “pcapy”: Pcapy is a Python extension module that interfaces with the libpcap packet capture library. Pcapy enables python scripts to capture packets on the network.
Python Module “xlrd”: Xlrd is a Python module that extracts data from Excel spreadsheets.
Python Module “threadpool”: Threadpool is a Python module that maintains a pool of worker threads to perform time consuming operations in parallel.

Please see installation instruction as the following:


.. code-block:: console

   apt-get install python3-pip
   pip3 install -r ../../requirements.txt

Setup and configure Scapy
~~~~~~~~~~~~~~~~~~~~~~~~~
Scapy is a powerful interactive packet manipulation program. It is able to forge or decode packets of a wide number of protocols, send them on the wire, capture them, match requests and replies, and much more. It can easily handle most classical tasks like scanning, tracerouting, probing, unit tests, attacks or network discovery.

DTS uses python module scapy to forge or decode packets of a wide number of protocols, send them over the wire, capture them, and analyse the packets.

.. code-block:: console

   pip3 install scapy

Install DPDK Test Suite on tester
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After configure environment, we need to install DPDK Test Suite into tester. First of all, download the latest DPDK Test Suite code from remote repo.

.. code-block:: console

   [root@tester ~]#  git clone http://dpdk.org/git/tools/dts
   [root@tester ~]#  cd dts
   [root@tester dts]#  ls
   [root@tester dts]# conf  dep  doc  dts  executions  framework  nics  output  test_plans  tests  tools

High Precision Timer (HPET) must be enabled in the platform BIOS if the HPET is to be used. Otherwise, the Time Stamp Counter (TSC) is used by default. The user can then navigate to the HPET option. On the Crystal Forest platform BIOS, the path is:
**Advanced -> PCH-IO Configuration -> High Precision Timer**

The DPDK Test Suite is composed of several file and directories:

*   dts: Main module of DPDK Test Suite suite
*   exectution.cfg: configuration file of DPDK Test Suite suite
*   framework: folder with dts framework modules
*   nics: folder with different network device modules
*   output: folder which contain running log files and result files
*   test_plans: folder with rst files which contain the description of test case
*   tests: folder with test case scripts

Setup Target Environment
------------------------

This section describes how to deploy DPDK Test Suite packages into DUT target.So far, DPDK Test Suite supports the following OS on DUT:

*   Fedora 32
*   Ubuntu 16.04/18.04/20.04
*   FreeBSD 12.1
*   RedHat 7.7/8.0
*   SUSE 15
*   Centos 7.7/8.0
*   OpenWRT 19.07

Before run DPDK Test Suite on target, we need to configure target environment, it includes BIOS setting, Network configure, compiler environment, etc.

BIOS setting Prerequisite
~~~~~~~~~~~~~~~~~~~~~~~~~

In general, enter BIOS Menu by pressing F2 while the platform is starting up.

.. note::
   It is strongly recommended to use DPDK with the latest generation of Intel platforms and processors.

The High Precision Timer (HPET) must be enabled in the platform BIOS if the HPET is to be used. Otherwise, the Time Stamp Counter (TSC) is used by default. The user can then navigate to the HPET option. On the Crystal Forest platform BIOS, the path is:

**Advanced -> PCH-IO Configuration -> High Precision Timer**

Enhanced Intel SpeedStep® Technology must be disabled in the platform BIOS, to ensure the processor voltage and core frequency do not change. This is necessary for consistency of data. On the Crystal Forest platform BIOS the path is:


**Advanced -> Processor Configuration -> Enhanced Intel SpeedStep**

Processor state C3 and C6 must be disabled for performance measure too. On the Crystal Forest platform BIOS, the path is:

**Advanced -> Processor Configuration -> Processor C3**
**Advanced -> Processor Configuration -> Processor C6**

Hyper-Threading Technology must be enabled. On the Crystal Forest platform BIOS, the path is:

**Advanced -> Processor Configuration -> Intel® Hyper-Threading Tech**

If the platform BIOS has any particular performance option, select the settings for best performance.

DPDK running Prerequisite
~~~~~~~~~~~~~~~~~~~~~~~~~
Compilation of DPDK need GNU maker, gcc, libc-header, kernel header installed. For 32-bit compilation on 64-bit systems, there’re some additional packages required. For Intel® C++ Compiler (icc) additional libraries may be required. For more detail information of required packets, please refer to Data Plane Development Kit Getting Started Guide.

The  DPDK igb_uio kernel module depends on traditional Linux kernel ``uio`` support to operate. Linux traditional ``uio`` support may be compiled as a module, so this module should be loaded using the ``modprobe`` program.
Kernel must support the allocation of hugepages. Hugepage support is required for the large memory pool allocation used for packet buffers. By using hugepage allocations, performance will be improved  since only fewer pages are needed, and therefore less Translation Lookaside Buffers (TLBs, high speed translation caches), which reduce the time it takes to translate a virtual page address to a physical page address. Without hugepages, high TLB miss rates would occur, slowing performance.

For more detail information of system requirements, also refer to `Data Plane Development Kit Getting Started Guide <http://dpdk.org/doc/guides>`_.

Authorized login session
------------------------
In DPDK Test Suite, support communication be established based on authorized ssh session. All ssh connection to each other will skip password interactive phase if remote server has been authorized.

In tester, you can use tool ssh-copy-id to save local available keys on DUT, thus create authorise login session between tester and DUT. By the same way, you can create authorise login session between tester and itself.

.. code-block:: console

   ssh-copy-id -i “IP of DUT”
   ssh-copy-id -i “IP of tester”

In DUT, You also can use tool ssh-copy-id to save local available keys in tester, thus create authorise login session between DUT and tester.

.. code-block:: console

   ssh-copy-id –i “IP of Tester”

