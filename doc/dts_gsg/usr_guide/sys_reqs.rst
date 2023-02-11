System Requirements
===================

This chapter describes the packages required to deploy DTS, including Tester and DUT.
Tester and DUT should have one interface connected to the same internet, so that they can be accessed by each other from local IP address.
The tester and DUT are recommended to install the latest Centos, Redhat or Ubuntu for easily installing DTS(DPDK Test Suite) or DPDK required modules.

.. note::

   Uubuntu 20.04 are installed for Tester and DUT, and  The setup instruction and required packages may be different on different operation systems.

Firewall should be disabled on Tester and DUT so that all packets can be accepted by NIC Interface.

.. code-block:: console

   systemctl disable firewalld.service


SSH Service
-----------

Since DPDK Test Suite Tester communicates with DUT via SSH, please install and start sshd service in your Tester and DUT.

.. code-block:: console

   apt-get install openssh-server      # download / install ssh software
   service ssh start                   # start ssh service

Generally DTS use Linux username and password to login, but it also supports to use authorized login.
For create authorized login session, user needs to generate RSA authentication keys to ssh connectioni:

.. code-block:: console

   ssh-keygen -t rsa

Python modules
--------------

To run DTS, `Python3` must be installed, and it uses the following packages:

* xlwt: it is used to generate spreadsheet files which compatible with MS Excel 97/2000/XP/2003 XLS files。
* numpy: it provides method to deal with array-processing test results.
* pexpect: it provides API to automate interactive SSH sessions.
* docutils：it is a modular system for processing documentation into useful formats, such as HTML, XML, and LaTeX
* pcapyplus: it is a Python extension module that interfaces with the libpcap packet capture library. Pcapyplus enables python scripts to capture packets on the network.
* xlrd: it is a Python module that extracts data from Excel spreadsheets.
* threadpool: it is a Python module that maintains a pool of worker threads to perform time consuming operations in parallel.
* scapy: it is a Python program that enables the user to send, sniff and dissect and forge network packets.

They are recorded in `requirements.txt`.

.. code-block:: console

   [root@tester ~]# cat requirements.txt
    ...
    xlwt==1.3.0
    pexpect==4.7.0
    numpy==1.24.2
    docutils
    pcapyplus
    xlrd
    scapy==2.4.4
    threadpool

Recommend installing them quickly with following commands:

.. code-block:: console

   apt-get install python3-pip
   pip3 install -r ../requirements.txt

DTS uses python module scapy to forge or decode packets of a wide number of protocols, send them over the wire, capture them, and analyse the packets.
We recommend installing scapy-2.4.4, as some protocol such as PFCP, GTPPDUSessionContainer are supported from this version.

.. code-block:: console

   pip3 install scapy  # install default version
   pip3 install scapy==2.4.4 # install specific version

Here are some differences between scapy 2.4.4 and scapy 2.4.3 about the packet layer:

.. table:: Differences between scapy 2.4.3 with scapy 2.4.4

    +------------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------------+
    | Layer                  | packet in scapy 2.4.3           | packet in scapy 2.4.4                         | Comments                                              |
    +========================+=================================+===============================================+=======================================================+
    | PPP                    | PPP(proto=0xc021)               | PPP(b\'\\xc0\\x21\')                          | PPP protocol filed length is 1 byte in scapy2.4.4     |
    +------------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------------+
    | L2TP                   | L2TP(\'\\x00\\x00\\x00\\x11\')  | L2TP(b\'\\x00\\x00\\x00\\x11\')               | L2TP is byte type in scapy2.4.4                       |
    +------------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------------+
    | PFCP                   | N/A                             | PFCP(S=1, seid=1)                             | PFCP is not supported in scapy2.4.3                   |
    +------------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------------+
    | GTPPDUSessionContainer | N/A                             | GTPPDUSessionContainer(type=0, P=1, QFI=0x34) | GTPPDUSessionContainer is not supported in scapy2.4.3 |
    +------------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------------+

BIOS Setting Prerequisite on x86
--------------------------------

For the majority of platforms, no special BIOS settings for Tester and DUT.
DPDK prefers devices bound to ``vfio-pci`` kernel module, therefore, `VT-x` and `VT-d` should be enabled.

.. code-block:: console

   Advanced -> Integrated IO Configuration -> Intel(R) VT for Directed I/O <Enabled>
   Advanced -> Processor Configuration -> Intel(R) Virtualization Technology <Enabled>

DPDK running Prerequisite
-------------------------

Hugepage support is required for the large memory pool allocation used for packet buffers.
DPDK performance will be imporved more with 1G page size than 2M, therefore, recommend to use 1G pages for DPDK.
The following options should be passed to Linux Cmdline:

.. code-block:: console

   hugepagesz=1G hugepages=16 default_hugepagesz=1G

For more detail information of DPDK requirements, please refer to `Data Plane Development Kit Getting Started Guide <http://dpdk.org/doc/guides>`_.

Performance testing requirements
--------------------------------

DTS supports three kinds of traffic generators: `Scapy`, `TRex` and `Ixia IxExplorer`. Scapy is for functional testing, TRex and `Ixia IxExplorer` are for performance testing. The mechanism in DTS that mananges traffic generators for performance is called `Pktgen`.

`Ixia IxExplorer` is the principal means used to program Ixia hardware and to perform testing on network devices. Ixia is a hardware traffic generator product of `keysight <https://www.keysight.com>`_ company. DTS requires to install TCL (Tool Command Language) package to connect and control `Ixia IxExplorer`:

.. code-block:: console

   apt-get install tcl

`TRex <https://trex-tgn.cisco.com>`_ is an open source software traffic generator fuelled by DPDK. It generates L3-7 traffic and provides in one tool capabilities. DTS requires to install `Trex` and configure it before lunching DTS.
