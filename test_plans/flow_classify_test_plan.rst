.. Copyright (c) <2019>, Intel Corporation
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

   - Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

   - Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.

   - Neither the name of Intel Corporation nor the names of its
     contributors may be used to endorse or promote products derived
     from this software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
   COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
   OF THE POSSIBILITY OF SUCH DAMAGE.

=============
flow classify
=============

This document provides test plan for flow classify feature.

Flow Classify provides flow record information with some measured properties.

DPDK provides a Flow Classification library that provides the ability
to classify an input packet by matching it against a set of Flow rules.
The implementation supports counting of IPv4 5-tuple packets which match a
particular Flow rule only.

example/flow_classify is the tool to call flow_classify lib for group of packets,
just after receiving them or before transmitting them. It is intended as a
demonstration of the basic components of a DPDK forwarding application which uses
the Flow Classify library API's.

DPDK technical doc refer to::

    dpdk/doc/guides/sample_app_ug/flow_classify.rst
    dpdk/doc/guides/prog_guide/flow_classify_lib.rst

Prerequisites
-------------
2xNICs (2 full duplex optical ports per NIC)
Flow Classify should run on 2 pair link peer at least.

i40e driver nic:
Ethernet Controller X710 for 10GbE SFP+ 1572
Ethernet Controller XXV710 for 25GbE SFP28 158b
Ethernet Controller XL710 for 40GbE QSFP+ 1583

ixgbe driver nic:
82599ES 10-Gigabit SFI/SFP+ Network Connection 10fb

HW configuration
----------------
link peer topology::

            Tester                          DUT
          .-------.                      .-------.
          | port0 | <------------------> | port0 |
          | port1 | <------------------> | port1 |
          '-------'                      '-------'

Stream configuration
--------------------
five valid streams(as examples/flow_classify/ipv4_rules_file.txt),
three invalid streams are the streams beyond config file.

UDP_1::

    Frame Data/Protocols: Ethernet 2 0800, IPv4,UDP/IP, Fixed 64.
    IPv4 Header Page: Dest Address: 2.2.2.7 Src  Address: 2.2.2.3
    UDP Header: Src Port: 32  Dest Port: 33

.. code-block:: console

    Ether()/IP (proto='udp', src='2.2.2.3', dst='2.2.2.7')/UDP(sport=32, dport=33)/Raw()

UDP_2::

    Frame Data/Protocols: Ethernet 2 0800, IPv4,UDP/IP, Fixed 64.
    IPv4 Header Page: Dest Address: 9.9.9.7 Src  Address: 9.9.9.3
    UDP Header: Src Port: 32  Dest Port: 33

.. code-block:: console

    Ether()/IP (proto='udp', src='9.9.9.3', dst='9.9.9.7')/UDP(sport=32, dport=33)/Raw()

UDP_invalid::

    Frame Data/Protocols: Ethernet 2 0800, IPv4,UDP/IP, Fixed 64.
    IPv4 Header Page: Dest Address: 9.8.7.6 Src  Address: 192.168.0.36
    UDP Header: Src Port: 10  Dest Port: 11

.. code-block:: console

    Ether()/IP (proto='udp', src='9.8.7.6', dst='192.168.0.36')/UDP(sport=10, dport=11)/Raw()

TCP_1::

    Frame Data/Protocols: Ethernet 2 0800, IPv4,TCP/IP, Fixed 64.
    IPv4 Header Page: Dest Address: 9.9.9.7 Src  Address: 9.9.9.3
    TCP Header: Src Port: 32  Dest Port: 33

.. code-block:: console

    Ether()/IP (proto='tcp', src='9.9.9.3', dst='9.9.9.7')/TCP(sport=32, dport=33)/Raw()

TCP_2::

    Frame Data/Protocols: Ethernet 2 0800, IPv4,TCP/IP, Fixed 64.
    IPv4 Header Page: Dest Address: 9.9.8.7 Src  Address: 9.9.8.3
    TCP Header: Src Port: 32  Dest Port: 33

.. code-block:: console

    Ether()/IP (proto='tcp', src='9.9.8.3', dst='9.9.8.7')/TCP(sport=32, dport=33)/Raw()

TCP_invalid::

    Frame Data/Protocols: Ethernet 2 0800, IPv4,TCP/IP, Fixed 64.
    IPv4 Header Page: Dest Address: 9.8.7.6 Src  Address: 192.168.0.36
    TCP Header: Src Port: 10  Dest Port: 11

.. code-block:: console

    Ether()/IP (proto='tcp', src='9.8.7.6', dst='192.168.0.36')/TCP(sport=10, dport=11)/Raw()

SCTP_1::

    Frame Data/Protocols: Ethernet 2 0800, IPv4, None, Fixed 256.
    IPv4 Header Page: Dest Address: 2.3.4.5 Src  Address: 6.7.8.9
    SCTP Header: Src Port: 32  Dest Port: 33
    Protocol: 132-SCTP

.. code-block:: console

    Ether()/IP (proto='sctp', src='6.7.8.9', dst='2.3.4.5')/SCTP(sport=32, dport=33)/Raw()

SCTP_invalid::

    Frame Data/Protocols: Ethernet 2 0800, IPv4, None, Fixed 256.
    IPv4 Header Page: Dest Address: 9.8.7.6 Src  Address: 192.168.0.36
    SCTP Header: Src Port: 10  Dest Port: 11
    Protocol: 132-SCTP

.. code-block:: console

    Ether()/IP (proto='sctp', src='9.8.7.6', dst='192.168.0.36')/SCTP(sport=10, dport=11)/Raw()


Compilation:
------------
steps::

    cd $DPDK_PATH
    export RTE_TARGET=$DPDK_PATH
    export RTE_SDK=`pwd`
    make -C examples/flow_classify

Flow classify bin file under::

    $DPDK_PATH/examples/flow_classify/build/flow_classify

rule config file(default)::

    $DPDK_PATH/examples/flow_classify/ipv4_rules_file.txt

Test cases
----------
The idea behind the testing process is to compare packet count sending by
ixia packet generator with packet count filtered by flow_classify. Valid
packets should be in flow_classify output and invalid packets should be ignored.
The rules are configured in a txt file. Testing content includes single
udp/tcp/sctp stream and multiple streams.

Test Case : check valid rule with udp stream
============================================
Send 32 packets of valid stream(as UDP_1 or UDP_2 in Stream configuration),
then check the total received packets in flow_classify's output message.

steps:

#. boot up flow_classify::

    ./dpdk-flow_classify -c 4 -n 4 -- --rule_ipv4=<rule config file>

#. send stream by packet generator(e.g. scapy or ixia)::

    scapy> sendp(UDP_1, iface='xxxxx', count=32)

#. check flow_classify output contain the following message::

    rule[0] count=1
    or
    rule[1] count=1

Test Case : check invalid rule with udp stream
==============================================
Send 32 packets of invalid stream(as UDP_invalid in Stream configuration),
then check flow_classify's output message has no count message

steps:

#. boot up flow_classify::

    ./dpdk-flow_classify -c 4 -n 4 -- --rule_ipv4=<rule config file>

#. send stream by packet generator(e.g. scapy or ixia)::

    scapy> sendp(UDP_invalid, iface='xxxxx', count=32)

#. check flow_classify output has no message as "rule[xxx] count=xxx", such as::

     rule[0] count=1

Test Case : check valid rule with tcp stream
============================================
Send 32 packets of valid stream(as TCP_1 or TCP_2 in Stream configuration),
then check the total received packets in flow_classify's output message.

steps:

#. boot up flow_classify::

    ./dpdk-flow_classify -c 4 -n 4 -- --rule_ipv4=<rule config file>

#. send stream by packet generator(e.g. scapy or ixia)::

    scapy> sendp(TCP_1, iface='xxxxx', count=32)

#. check flow_classify output contain the following message::

    rule[2] count=1
    or
    rule[3] count=1

Test Case : check invalid rule with tcp stream
==============================================
Send 32 packets of invalid stream(as TCP_invalid in Stream configuration),
then check flow_classify's output message has no count message.

steps:

#. boot up flow_classify::

    ./dpdk-flow_classify -c 4 -n 4 -- --rule_ipv4=<rule config file>

#. send stream by packet generator(e.g. scapy or ixia)::

    scapy> sendp(TCP_invalid, iface='xxxxx', count=32)

#. check flow_classify output has no message as "rule[xxx] count=xxx", such as::

    rule[2] count=1

Test Case : check valid rule with sctp stream
=============================================
Send 32 packets of valid stream(as SCTP_1 in Stream configuration),
then check the total received packets in flow_classify's output message.

steps:

#. boot up flow_classify::

    ./dpdk-flow_classify -c 4 -n 4 -- --rule_ipv4=<rule config file>

#. send stream by packet generator(e.g. scapy or ixia)::

    scapy> sendp(SCTP_1, iface='xxxxx', count=32)

#. check flow_classify output contain the following message::

    rule[4] count=1

Test Case : check invalid rule with sctp stream
===============================================
Send 32 packets of invalid stream(as SCTP_invalid in Stream configuration),
then check flow_classify's output message has no count message.

steps:

#. boot up flow_classify::

    ./dpdk-flow_classify -c 4 -n 4 -- --rule_ipv4=<rule config file>

#. send stream by packet generator(e.g. scapy or ixia)::

    scapy> sendp(SCTP_invalid, iface='xxxxx', count=32)

#. check flow_classify output has no "rule[xxx] count=xxx" message, such as::

    rule[4] count=1

Test Case: check valid/invalid rule with multiple streams
=========================================================
Send multiple streams, 32 packets/each stream type(all stream types in Stream configuration),
then check if they are filtered/captured by flow_classify.

steps:

#. boot up flow_classify::

    ./dpdk-flow_classify -c 4 -n 4 -- --rule_ipv4=<rule config file>

#. send multiple stream by packet generator(e.g. scapy or ixia), include SCTP_1/SCTP_invalid/TCP_invalid/TCP_1/TCP_2/UDP_invalid/UDP_1/UDP_2::

    scapy> multiple_stream = [SCTP_1, SCTP_invalid, TCP_invalid, TCP_1, TCP_2, UDP_invalid, UDP_1, UDP_2]
    scapy> sendp(multiple_stream, iface='xxxx', count=32)

#. check flow_classify output only contain the following count message::

    rule[0] count=1
    rule[1] count=1
    rule[2] count=1
    rule[3] count=1
    rule[4] count=1
