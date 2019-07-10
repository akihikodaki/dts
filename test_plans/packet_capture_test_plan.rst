.. Copyright (c) <2010-2019> Intel Corporation
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

==============
packet capture
==============

Packet capture framework feature support packet capturing on dpdk ethernet
devices. DPDK provides dpdk-pdump tool under app/pdump directory for packet
capturing on dpdk.

The dpdk-pdump application will act as the secondary process. The EAL thread
polls for packet capture fd. If fd polled matches packet capture fd, it will
initiate packet capture processing.

The testpmd application will act as the primary process. The primary process
create socket for packet capture connection with the secondary process and
registers socket with packet capture epoll event. Packet capture event will
be polled as part of interrupt thread.

The primary process creates mempool and two rte_rings for packets duplication
and sharing packet info with the secondary process respectively.

Upon receiving packet capture event, the primary process receive either
register RX/TX callbacks or remove RX/TX callbacks message from the secondary
process on socket.If packet matches, reference count of packet will be
incremented and enqueued to second rte_ring for the secondary process to use.

DPDK technical doc refer to::

   dpdk/doc/guides/tools/pdump.rst

Prerequisites
=============

2x NICs (2 full duplex ports per NIC) plugged into the available slots on a
platform, another two nic ports are linked with cables.

Connections ports between TESTER and DUT::

       TESTER                                DUT
                    physical link
     .--------.                          .--------.
     | portA0 | <----------------------> | portB0 |
     |        |                          |        |
     | portA1 | <----------------------> | portB1 |
     '--------'                          |        |
                                 ------> | portB2 |
                                |        |        |
                                 ------> | portB3 |
                                         '--------'

note: portB0/portB1 are the binded ports.
      portB2/portB3 keep link up status and don't bind to dpdk driver.
      Except portB0/portB1, DUT should have other two ports on link up status

Test cases
==========

The testpmd application act as server process with port-topology chained mode,
the dpdk-pdump act as client process to dump capture packet with different
options setting. Select one port of tester as tx port, another port of tester
as rx port, send different type packets from two ports, check pcap file
content dumped by scapy and tcpdump to confirm testpmd working correctly,
check pcap file content dumped by tcpdump and dpdk-pdump to confirm
dpdk-pdump working correctly.

dpdk-pdump command format
-------------------------

#. packet capture framework tool dpdk-pdump command format, parameters inside
the parenthesis represents the mandatory parameters, parameters inside the
square brackets represents optional

parameters::

    ./app/dpdk-pdump -- --pdump=
    '(port = <port_id> |device_id = <pci address>),
    (queue=<queue number>),
    (rx-dev=<iface/path to pcap file> | tx-dev=<iface/path to pcap file>),
    [ring-size=<size>],
    [mbuf-size=<size>],
    [total-num-mbufs=<size>]'

transmission packet format
--------------------------

#. IP_RAW::

    [Ether()/IP()/Raw('\0'*60)]

#. TCP::

    [Ether()/IP()/TCP()/Raw('\0'*60)]

#. UDP::

    [Ether()/IP()/UDP()/Raw('\0'*60)]

#. SCTP::

    [Ether()/IP()/SCTP()/Raw('\0'*40)]

#. IPv6_TCP::

    [Ether()/IPv6()/TCP()/Raw('\0'*60)]

#. IPv6_UDP::

    [Ether()/IPv6()/UDP()/Raw('\0'*60)]

#. IPv6_SCTP::

    [Ether()/IP()/IPv6()/SCTP()/Raw('\0'*40)]

#. VLAN_UDP::

    [Ether()/Dot1Q()/IP()/UDP()/Raw('\0'*40)]

#. TIMESYNC::

    [Ether(dst='FF:FF:FF:FF:FF:FF',type=0x88f7)/"\\x00\\x02"]

#. ARP::

    [Ether(dst='FF:FF:FF:FF:FF:FF')/ARP()]

#. LLDP(LLDP()/LLDPManagementAddress() method are in dts/dep/lldp.py)::

    [Ether()/LLDP()/LLDPManagementAddress()]

port configuration
------------------

#. confirm two NICs physical link on a platform::

    dut port 0 <---> tester port 0
    dut port 1 <---> tester port 1

#. Bind two port on DUT::

    ./usertools/dpdk_nic_bind.py --bind=igb_uio <dut port 0 pci address> <dut port 1 pci address>

#. On dut, use port 0 as rx/tx port. If dut port 0 rx dump is set, scapy send
   packet from tester port 0 and tcpdump dumps tester port 1's packet. If dut
   port 0 tx dump is set, scapy send packet from tester port 1 and tcpdump dumps
   tester port 0's packet.

#. If using interfaces as dpdk-pdump vdev, prepare two ports on DUT, which
   haven't been binded to dpdk and have been in linked status

Test Case: test pdump port
==========================

Test different port type definition options::

    port=<dut port id>
    device_id=<dut pci address>

steps:

#. Boot up dpdk's testpmd with chained option::

    ./app/testpmd -c 0x6 -n 4 -- -i --port-topology=chained
    testpmd> set fwd io
    testpmd> start

#. When test VLAN_UDP type packet transmission, set vlan::

    testpmd> vlan set filter off 1
    testpmd> start

#. Boot up dpdk-pdump::

    ./app/dpdk-pdump -- --pdump  '<port option>,queue=*,\
    tx-dev=/tmp/pdump-tx.pcap,rx-dev=/tmp/pdump-rx.pcap'

#. Set up linux's tcpdump to receiver packet on tester::

    tcpdump -i <rx port name> -w /tmp/sniff-<rx port name>.pcap
    tcpdump -i <tx port name> -w /tmp/sniff-<tx port name>.pcap

#. Send packet on tester by port 0::

    sendp(<packet format>, iface=<port 0 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
file dumped by dpdk-pdump with pcap files dumped by tcpdump.

#. Send packet on tester by port 1::

    sendp(<packet format>, iface=<port 1 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
file dumped by dpdk-pdump with pcap files dumped by tcpdump::

    pkt=rdpcap('xxxx1.pcap')
    pkt[0].show2()
    pkt=rdpcap('xxxx2.pcap')
    pkt[0].show2()


Test Case: test pdump queue
===========================

Capture first queue traffic.

test different queue options::

    first queue 'queue=0'
    all queue 'queue=*'

steps:

#. Boot up dpdk's testpmd with chained option::

    ./app/testpmd -c 0x6 -n 4 -- -i --port-topology=chained
    testpmd> set fwd io
    testpmd> start

#. When test VLAN_UDP type packet transmission, set vlan::

    testpmd> vlan set filter off 1
    testpmd> start

#. Boot up dpdk-pdump::

    ./app/dpdk-pdump -- --pdump  'port=0,<queue option>,\
    tx-dev=/tmp/pdump-tx.pcap,rx-dev=/tmp/pdump-rx.pcap'

#. Set up linux's tcpdump to receiver packet on tester::

    tcpdump -i <rx port name> -w /tmp/sniff-<rx port name>.pcap
    tcpdump -i <tx port name> -w /tmp/sniff-<tx port name>.pcap

#. Send packet on tester by port 0::

    sendp(<packet format>, iface=<port 0 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
   file dumped by dpdk-pdump with pcap files dumped by tcpdump.

#. Send packet on tester by port 1::

    sendp(<packet format>, iface=<port 1 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
   file dumped by dpdk-pdump with pcap files dumped by tcpdump::

    pkt=rdpcap('xxxx1.pcap')
    pkt[0].show2()
    pkt=rdpcap('xxxx2.pcap')
    pkt[0].show2()


Test Case: test pdump dev pcap
==============================

Dump rx/tx transmission packets into a specified pcap files.

test different dump options::

    tx-dev=/tmp/pdump-tx.pcap,rx-dev=/tmp/pdump-rx.pcap
    rx-dev=/tmp/pdump-rx.pcap
    tx-dev=/tmp/pdump-tx.pcap

steps:

#. Boot up dpdk's testpmd with chained option::

    ./app/testpmd -c 0x6 -n 4 -- -i --port-topology=chained
    testpmd> set fwd io
    testpmd> start

#. When test VLAN_UDP type packet transmission, set vlan(other packet ignore this step)::

    testpmd> vlan set filter off 1
    testpmd> start

#. Boot up dpdk-pdump with pdump options::

    ./app/dpdk-pdump -- --pdump  'port=0,queue=*,<dump object>'

#. Set up linux's tcpdump to receiver packet on tester::

    tcpdump -i <rx port name> -w /tmp/sniff-<rx port name>.pcap
    tcpdump -i <tx port name> -w /tmp/sniff-<tx port name>.pcap

#. Send packet on tester by port 0::

    sendp(<packet format>, iface=<port 0 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
   file dumped by dpdk-pdump with pcap files dumped by tcpdump(ignore when only
   set tx-dev).

#. Send packet on tester by port 1::

    sendp(<packet format>, iface=<port 1 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
   file dumped by dpdk-pdump with pcap files dumped by tcpdump(ignore when only
   set rx-dev)::

    pkt=rdpcap('xxxx1.pcap')
    pkt[0].show2()
    pkt=rdpcap('xxxx2.pcap')
    pkt[0].show2()


Test Case: test pdump dev iface
===============================

Dump rx/tx transmission packets to a specified port, which is on link status.

test different dump options::

    tx-dev=<dut tx port name>,rx-dev=<dut rx port name>
    rx-dev=<dut rx port name>
    tx-dev=<dut tx port name>

steps:

#. Boot up dpdk's testpmd with chained option::

    ./app/testpmd -c 0x6 -n 4 -- -i --port-topology=chained
    testpmd> set fwd io
    testpmd> start

#. When test VLAN_UDP type packet transmission, set vlan(other packet ignore this step)::

    testpmd> vlan set filter off 1
    testpmd> start

#. Boot up dpdk-pdump with pdump options::

    ./app/dpdk-pdump -- --pdump  'port=0,queue=*,<dump object>'

#. Set up linux's tcpdump to receiver packet on tester::

    tcpdump -i <rx port name> -w /tmp/sniff-<rx port name>.pcap
    tcpdump -i <tx port name> -w /tmp/sniff-<tx port name>.pcap

#. Set up linux's tcpdump to receiver packet of dpdk-pdump on Dut::

    when rx-dev is set, use 'tcpdump -i <dut rx port name> -w /tmp/pdump-rx.pcap'
    when tx-dev is set, use 'tcpdump -i <dut tx port name> -w /tmp/pdump-tx.pcap'

#. Send packet on tester by port 0::

    sendp(<packet format>, iface=<port 0 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
   file dumped by dpdk-pdump with pcap files dumped by tcpdump(ignore when only
   set tx-dev).

#. Send packet on tester by port 1::

    sendp(<packet format>, iface=<port 1 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
   file dumped by dpdk-pdump with pcap files dumped by tcpdump(ignore when only
   set rx-dev)::

    pkt=rdpcap('xxxx1.pcap')
    pkt[0].show2()
    pkt=rdpcap('xxxx2.pcap')
    pkt[0].show2()


Test Case: test pdump ring size
===============================

Test ring size option, set value within 2^[1~27].

steps:

#. Boot up dpdk's testpmd with chained option::

    ./app/testpmd -c 0x6 -n 4 -- -i --port-topology=chained
    testpmd> set fwd io
    testpmd> start

#. When test VLAN_UDP type packet transmission, set vlan::

    testpmd> vlan set filter off 1
    testpmd> start

#. Boot up dpdk-pdump with pdump options::

    ./app/dpdk-pdump -- --pdump  'port=0,queue=*,\
    tx-dev=/tmp/pdump-tx.pcap,rx-dev=/tmp/pdump-rx.pcap,ring-size=1024'

#. Set up linux's tcpdump to receiver packet on tester::

    tcpdump -i <rx port name> -w /tmp/sniff-<rx port name>.pcap
    tcpdump -i <tx port name> -w /tmp/sniff-<tx port name>.pcap

#. Send packet on tester by port 0::

    sendp(<packet format>, iface=<port 0 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
   file dumped by dpdk-pdump with pcap files dumped by tcpdump.

#. Send packet on tester by port 1::

    sendp(<packet format>, iface=<port 1 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
   file dumped by dpdk-pdump with pcap files dumped by tcpdump::

    pkt=rdpcap('xxxx1.pcap')
    pkt[0].show2()
    pkt=rdpcap('xxxx2.pcap')
    pkt[0].show2()


Test Case: test pdump mbuf size
===============================

Test mbuf size option, set value within [252~50000]. min value is decided by
single packet size, max value is decided by test platform memory size.

steps:

#. Boot up dpdk's testpmd with chained option::

    ./app/testpmd -c 0x6 -n 4 -- -i --port-topology=chained
    testpmd> set fwd io
    testpmd> start

#. When test VLAN_UDP type packet transmission, set vlan::

    testpmd> vlan set filter off 1
    testpmd> start

#. Boot up dpdk-pdump with pdump options::

    ./app/dpdk-pdump -- --pdump  'port=0,queue=*,\
    tx-dev=/tmp/pdump-tx.pcap,rx-dev=/tmp/pdump-rx.pcap,mbuf-size=2048'

#. Set up linux's tcpdump to receiver packet on tester::

    tcpdump -i <rx port name> -w /tmp/sniff-<rx port name>.pcap
    tcpdump -i <tx port name> -w /tmp/sniff-<tx port name>.pcap

#. Send packet on tester by port 0::

    sendp(<packet format>, iface=<port 0 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
   file dumped by dpdk-pdump with pcap files dumped by tcpdump.

#. Send packet on tester by port 1::

    sendp(<packet format>, iface=<port 1 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
   file dumped by dpdk-pdump with pcap files dumped by tcpdump::

    pkt=rdpcap('xxxx1.pcap')
    pkt[0].show2()
    pkt=rdpcap('xxxx2.pcap')
    pkt[0].show2()


Test Case: test pdump total num mbufs
=====================================

Test total-num-mbufs option, set value within [1025~65535]

steps:

#. Boot up dpdk's testpmd with chained option::

    ./app/testpmd -c 0x6 -n 4 -- -i --port-topology=chained
    testpmd> set fwd io
    testpmd> start

#. When test VLAN_UDP type packet transmission, set vlan::

    testpmd> vlan set filter off 1
    testpmd> start

#. Boot up dpdk-pdump with pdump options::

    ./app/dpdk-pdump -- --pdump  'port=0,queue=*,\
    tx-dev=/tmp/pdump-tx.pcap,rx-dev=/tmp/pdump-rx.pcap,total-num-mbufs=8191'

#. Set up linux's tcpdump to receiver packet on tester::

    tcpdump -i <rx port name> -w /tmp/sniff-<rx port name>.pcap
    tcpdump -i <tx port name> -w /tmp/sniff-<tx port name>.pcap

#. Send packet on tester by port 0::

    sendp(<packet format>, iface=<port 0 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
   file dumped by dpdk-pdump with pcap files dumped by tcpdump.

#. Send packet on tester by port 1::

    sendp(<packet format>, iface=<port 1 name>)

#. Compare pcap file of scapy with the pcap file dumped by tcpdump. Compare pcap
   file dumped by dpdk-pdump with pcap files dumped by tcpdump::

    pkt=rdpcap('xxxx1.pcap')
    pkt[0].show2()
    pkt=rdpcap('xxxx2.pcap')
    pkt[0].show2()