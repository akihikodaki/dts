.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021 Intel Corporation

===============================
IAVF: default RSS configuration
===============================

Description
===========

DPDK-21.02 improved iavf default RSS, major feature are:

 - support IAVF to use port config to set ip/udp/tcp/sctp RSS, other rss_type like gtpu/l2tpv3/esp/ah will be
   rejected, they should only be supported used in RTE_FLOW::

    port config all rss ip/udp/tcp/sctp

 - default RSS should be overwritten but not append, for example, set udp, then set tcp, it will be tcp at the end.
 - any kernel PF enabled default RSS should be disabled, it requires ice base driver >= 1.3.0.
 - only support Intel E810 series cards now, but not support Intel 700 series cards.

Prerequisites
=============

1. NIC requires:

   - Intel® Ethernet 800 Series: E810-XXVDA4/E810-CQ, etc.

2. insmod ice.ko, and bind PF to ice.

3. create a VF from a PF in DUT, set mac address for this VF::

    echo 1 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    ip link set enp24s0f0 vf 0 mac 00:11:22:33:44:55

4. bind VF to vfio-pci::

    modprobe vfio-pci
    usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:18:01.0

5. launch testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -- -i --rxq=16 --txq=16
    testpmd>set fwd rxonly
    testpmd>set verbose 1
    testpmd> start

Basic test steps
----------------

1. set rss function

* testpmd command-line options::

   --rss-ip: set ip RSS.
   --rss-udp: set udp RSS.
   --disable-rss: disable RSS.

  RSS is on by default.

* testpmd runtime functions::

   port config all rss ip/udp/tcp/sctp/none/all

  * The ``none`` option is equivalent to the ``--disable-rss`` command-line option.
  * The `` ip`` option is equivalent to the ``--rss-ip`` command-line option.
  * The `` udp`` option is equivalent to the ``--rss-udp`` command-line option.

.. note::

    - IP_RSS: ip/udp/tcp/sctp pkts use L3 ipv4()/ipv6() get hash values.
    - UDP(TCP/SCTP)_RSS: only UDP(TCP/SCTP) pkts use L4 UDP()/TCP()/SCTP() get hash values, other pkts have no hash values.

2. transmit different protocol packets, and check hash results based on following table. (take IP RSS for example)

 a. transmit MAC_IPV4_PAY packet::

      Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.3")/("X"*40)

 b. check hash results that `RSS hash=0x5bf8517c` in the output::

      testpmd> port 0/queue 12: received 1 packets(have hash)
      src=00:1E:67:56:C8:2B - dst=00:11:22:33:44:55 - type=0x0800 - length=74 - nb_segs=1 - RSS hash=0x5bf8517c - RSS
      queue=0xc - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 -
      l3_len=20 - Receive queue=0xc
      ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

 c. transmit MAC_IPV4_UDP packet::

      Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)

 d. check hash results that `RSS hash=0x5bf8517c` in the output, MAC_IPV4_UDP has same hash vaule with MAC_IPV4_PAY,
    that's becuse they have same IP dst and src::

      testpmd> port 0/queue 12: received 1 packets(have hash)
      src=00:1E:67:56:C8:2B - dst=00:11:22:33:44:55 - type=0x0800 - length=82 - nb_segs=1 - RSS hash=0x5bf8517c - RSS
      queue=0xc - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_UDP  - sw ptype: L2_ETHER L3_IPV4 L4_UDP  - l2_len=14 -
      l3_len=20 - l4_len=8 - Receive queue=0xc
      ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

.. note::

    Some packets don't have string `RSS hash` in the output, as their hash function are disabled.


.. table::

    +-------------------------------+------------------------------+--------------------------+-----------------------------+-------------------------+
    | Default hash function: Non Symmetric_toeplitz                                                                                                   |
    +-------------------------------+------------------------------+--------------------------+-----------------------------+-------------------------+
    | RSS Configuration	            | Pattern                      | Default Input Set        | Traffic packet type         | hash action             |
    +===============================+==============================+==========================+=============================+=========================+
    |                               | MAC_IPV4, MAC_IPV6           | ipv4, ipv6	              | MAC_IPV4_PAY                | record hash value       |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_UDP                | same hash value         |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_TCP                | same hash value         |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_SCTP               | same hash value         |
    |             IP                +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_PAY                | record hash value       |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_UDP                | same hash value         |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_TCP                | same hash value         |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_SCTP               | same hash value         |
    +-------------------------------+------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               | MAC_IPV4_UDP, MAC_IPV6_UDP   | ipv4-udp, ipv6-udp       | MAC_IPV4_UDP                | record hash value       |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_PAY                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_TCP                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_SCTP               | no hash value           |
    |             UDP               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_UDP                | record hash value       |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_PAY                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_TCP                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_SCTP               | no hash value           |
    +-------------------------------+------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               | MAC_IPV4_TCP, MAC_IPV6_TCP   | ipv4-tcp, ipv6-tcp       | MAC_IPV4_TCP                | record hash value       |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_PAY                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_UDP                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_SCTP               | no hash value           |
    |             TCP               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_TCP                | record hash value       |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_PAY                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_UDP                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_SCTP               | no hash value           |
    +-------------------------------+------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               | MAC_IPV4_SCTP, MAC_IPV6_SCTP | ipv4-sctp, ipv6-sctp     | MAC_IPV4_SCTP               | record hash value       |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_PAY                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_UDP                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_TCP                | no hash value           |
    |             SCTP              +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_SCTP               | record hash value       |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_PAY                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_UDP                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_TCP                | no hash value           |
    +-------------------------------+------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               | ALL                          | all                      | MAC_IPV4_PAY                | record hash value       |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_UDP                | different hash value    |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_TCP                | different hash value    |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_SCTP               | different hash value    |
    |             all               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_PAY                | record hash value       |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_UDP                | different hash value    |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_TCP                | different hash value    |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_SCTP               | different hash value    |
    +-------------------------------+------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_PAY                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_SCTP               | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_UDP                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_TCP                | no hash value           |
    |         none (disable)        +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_PAY                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_SCTP               | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_UDP                | no hash value           |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_TCP                | no hash value           |
    +-------------------------------+------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               | MAC_IPV4, MAC_IPV6           | ipv4, ipv6	              | MAC_IPV4_PAY                | record hash value       |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_SCTP               | same hash value         |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_UDP                | same hash value         |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV4_TCP                | same hash value         |
    |           w/o setting         +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_PAY                | record hash value       |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_SCTP               | same hash value         |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_UDP                | same hash value         |
    |                               +------------------------------+--------------------------+-----------------------------+-------------------------+
    |                               |                              |                          | MAC_IPV6_TCP                | same hash value         |
    +-------------------------------+------------------------------+--------------------------+-----------------------------+-------------------------+

Sending packets command line of scapy
-------------------------------------

.. table::

    +---------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+
    | Traffic packet type | Scapy command line                                                                                                                                        |
    +=====================+===========================================================================================================================================================+
    | MAC_IPV4_PAY        | sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.3")/("X" * 40)], iface="enp24s0f0")                                             |
    +---------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+
    | MAC_IPV4_UDP        | sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X" * 40)], iface="enp24s0f0")                  |
    +---------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+
    | MAC_IPV4_TCP        | sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X" * 40)], iface="enp24s0f0")                  |
    +---------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+
    | MAC_IPV4_SCTP       | sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X" * 40)], iface="enp24s0f0")                 |
    +---------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+
    | MAC_IPV6_PAY        | sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/("X" * 40)], iface="enp24s0f0")                             |
    +---------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+
    | MAC_IPV6_UDP        | sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X" * 40)], iface="enp24s0f0")  |
    +---------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+
    | MAC_IPV6_TCP        | sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X" * 40)], iface="enp24s0f0")  |
    +---------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+
    | MAC_IPV6_SCTP       | sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X" * 40)], iface="enp24s0f0") |
    +---------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+

Test Case: test_iavf_rss_configure_to_ip
========================================

Set rss to ip with testpmd runtime func, transmit different protocol packets, and check hash results.

Test Case: test_iavf_rss_configure_to_udp
=========================================

Set rss to udp with testpmd runtime func, transmit different protocol packets, and check hash results.

Test Case: test_iavf_rss_configure_to_tcp
=========================================

Set rss to tcp with testpmd runtime func, transmit different protocol packets, and check hash results.

Test Case: test_iavf_rss_configure_to_sctp
==========================================

Set rss to sctp with testpmd runtime func, transmit different protocol packets, and check hash results.

Test Case: test_iavf_rss_configure_to_all
=========================================

Set rss to all with testpmd runtime func, transmit different protocol packets, and check hash results.

Test Case: test_iavf_rss_configure_to_none
==========================================

disable rss with testpmd runtime func, transmit different protocol packets, and check hash results.

Test Case: test_iavf_rss_command_line_to_ip
===========================================

Set rss to ip with testpmd command line options, transmit different protocol packets, and check hash results.

Test Case: test_iavf_rss_command_line_to_udp
============================================

Set rss to udp with testpmd command line options, transmit different protocol packets, and check hash results.

Test Case: test_iavf_rss_command_line_to_none
=============================================

disable rss with testpmd command line options, transmit different protocol packets, and check hash results.

Test Case: test_iavf_rss_command_line_to_default
================================================

don't set rss with either runtime func nor command line option, only use default configuration, transmit different protocol packets, and check hash results.
