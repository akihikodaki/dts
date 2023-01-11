.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2019 Intel Corporation

==========================
Kernel PF + IAVF test plan
==========================

Intel Adaptive Virtual Function(IAVF) is aimed to provide a common VF for VM
which means just need one unified VF driver so you don't have to reload
different VF driver when you upgrade the PF NIC.
One of the advantages is you don't have to do any modification for code or
hardware for an existing VM image running on the new NIC.

Requirement
===========
This plan for IAVF only supports kernel PF scenario.

Hardware
========
ICE/I40E driver NIC.

Prerequisites
=============
Get the pci device id of DUT, for example::

    ./usertools/dpdk-devbind.py -s

    0000:18:00.0 'Device 1592' if=enp24s0f0 drv=ice unused=igb_uio
    0000:18:00.1 'Device 1592' if=enp24s0f1 drv=ice unused=igb_uio

If the drive support vf-vlan-pruning flag::
    ethtool --set-priv-flags $PF_INTF vf-vlan-pruning on

Create 1 VF from 1 kernel PF::

    echo 1 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs

Set VF mac as 00:01:23:45:67:89::

    ip link set $PF_INTF vf 0 mac 00:01:23:45:67:89

Test IAVF cases on host or in qemu

Bind VF device to igb_uio or vfio-pci

if test IAVF, start up VF port::

    ./<build_target>/app/dpdk-testpmd -c f -n 4 -- -i

if test DCF, set VF port to dcf and start up::

   Enable kernel trust mode:

       ip link set $PF_INTF vf 0 trust on

    ./<build_target>/app/dpdk-testpmd -c f -n 4 -a 0000:18:01.0,cap=dcf -- -i

.. note::

   make dcf as full feature pmd is dpdk22.07 feature, and only support E810 series nic.

Test case: VF basic RX/TX
=========================
Set rxonly forward, start testpmd

Send 100 random packets from tester, check packets can be received

Set txonly forward, start testpmd

Check tester could receive the packets from application generated

Test case: VF promisc
=====================
Enable kernel trust mode::

    ip link set $PF_INTF vf 0 trust on

Start VF testpmd, set mac forward and enable print output

Use scapy to send random packets with current VF0's MAC, verify the
packets can be received and forwarded by the VF.

Use scapy to send random packets with a wrong MAC to VF0, verify the
packets can be received and forwarded by the VF.

Disable promisc mode::

    testpmd> set promisc all off

Use scapy to send random packets with current VF0's MAC, verify the
packets can be received and forwarded by the VF.

Use scapy to send random packets with a wrong MAC to VF0, verify the
packets can't be received and forwarded by the VF.

Enable promisc mode::

    testpmd> set promisc all on

Use scapy to send random packets with current VF0's MAC, verify the
packets can be received and forwarded by the VF.

Use scapy to send random packets with a wrong MAC to VF0, verify the
packets can be received and forwarded by the VF.

Disable kernel trust mode::

    ip link set $PF_INTF vf 0 trust off

Test case: VF multicast
=======================
Disable kernel trust mode::

    ip link set $PF_INTF vf 0 trust off

Start VF testpmd

Disable promisc and multicast mode::

    testpmd> set promisc all off
    testpmd> set allmulti all off
    testpmd> start

Send packet with current VF0's MAC, and check VF can receive the packet.

Send packet with multicast MAC 01:80:C2:00:00:08, and check VF can not
receive the packet.

Enable multicast mode::

    testpmd> set allmulti all on

configure multicast address::

    testpmd> mcast_addr add 0 01:80:C2:00:00:08

Send packet with current VF0's MAC, and check VF can receive the packet.

Send packet with multicast MAC 01:80:C2:00:00:08, and check VF can
receive the packet.

Test case: VF broadcast
=======================
Disable VF promisc mode::

    testpmd> set promisc all off
    testpmd> start

Send packet with broadcast address ff:ff:ff:ff:ff:ff, and check VF can
receive the packet

Test case: VF vlan insertion
============================

Disable VF vlan strip::

    testpmd> vlan set strip off 0

Set vlan id 20 for tx_vlan::

    testpmd> port stop all
    testpmd> tx_vlan set 0 20
    testpmd> port start all
    testpmd> set fwd mac
    testpmd> start

Send normal packet::

    p=Ether(dst="00:01:23:45:67:89")/IP()/Raw(load='X'*30)

Verify packet that out from VF contains the vlan tag 20


Test case: VF vlan strip
========================

Enable VF vlan strip::

    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 20 0
    testpmd> vlan set strip on 0
    testpmd> set fwd mac
    testpmd> set verbose 1
    testpmd> start

Send packets with vlan tag::

    p=Ether(dst="00:01:23:45:67:89")/Dot1Q(id=0x8100,vlan=20)/IP()/Raw(load='X'*30)

Check that out from VF doesn't contain the vlan tag.

Disable VF vlan strip::

    testpmd> vlan set strip off 0

Send packets with vlan tag::

    Ether(dst="00:01:23:45:67:89")/Dot1Q(id=0x8100,vlan=20)/IP()/Raw(load='X'*30)

Check that out from VF contains the vlan tag.


Test case: VF RSS
=================

Start command with multi-queues like below::

   ./<build_target>/app/dpdk-testpmd -c f -n 4 -- -i --txq=4 --rxq=4

Show RSS RETA configuration::

    testpmd> show port 0 rss reta 64 (0xffffffffffffffff)

    RSS RETA configuration: hash index=0, queue=0
    RSS RETA configuration: hash index=1, queue=1
    RSS RETA configuration: hash index=2, queue=2
    RSS RETA configuration: hash index=3, queue=3
    ...
    RSS RETA configuration: hash index=60, queue=0
    RSS RETA configuration: hash index=61, queue=1
    RSS RETA configuration: hash index=62, queue=2
    RSS RETA configuration: hash index=63, queue=3

Config hash reta table::

    testpmd> port config 0 rss reta (0,3)
    testpmd> port config 0 rss reta (1,2)
    testpmd> port config 0 rss reta (2,1)
    testpmd> port config 0 rss reta (3,0)

Check RSS RETA configuration has changed::

    testpmd> show port 0 rss reta 64 (0xffffffffffffffff)

    RSS RETA configuration: hash index=0, queue=3
    RSS RETA configuration: hash index=1, queue=2
    RSS RETA configuration: hash index=2, queue=2
    RSS RETA configuration: hash index=3, queue=1

Enable IP/TCP/UDP RSS::

  testpmd> port config all rss (all|ip|tcp|udp|sctp|ether|port|vxlan|geneve|nvgre|none)

Send different flow types' IP/TCP/UDP packets to VF port, check packets are
received by different configured queues.

Test case: VF RSS hash key
==========================

Start command with multi-queues like below::

   ./<build_target>/app/dpdk-testpmd -c f -n 4 -- -i --txq=4 --rxq=4

Show port rss hash key::

    testpmd> show port 0 rss-hash key

Set rxonly fwd, enable print, start testpmd::

    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

Send ipv4 packets, mark the RSS hash value::

    p=Ether(dst="56:0A:EC:50:A4:28")/IP(src="1.2.3.4")/Raw(load='X'*30)

Update ipv4 different hash key::

    testpmd> port config 0 rss-hash-key ipv4 1b9d58a4b961d9cd1c56ad1621c3ad51632c16a5d16c21c3513d132c135d132c13ad1531c23a51d6ac49879c499d798a7d949c8a

Show port rss hash key, check the key is same to configured key::

    testpmd> show port 0 rss-hash key
    RSS functions:
     all ipv4 ipv6 ip
    RSS key:
    1B9D58A4B961D9CD1C56AD1621C3AD51632C16A5D16C21C3513D132C135D132C13AD1531C23A51D6AC49879C499D798A7D949C8A

Send ipv4 packets, check RSS hash value is different::

    p=Ether(dst="56:0A:EC:50:A4:28")/IP(src="1.2.3.4")/Raw(load='X'*30)

Test case: VF port stop/start
=============================

Stop VF port::

    testpmd> port stop all

Start VF port::

    testpmd> port start all

Repeat above stop and start port for 10 times

Send packets from tester

Check VF could receive packets


Test case: VF statistics reset
==============================

Check VF port stats::

    testpmd> show port stats all

Clear VF port stats::

    testpmd> clear port stats all

Check VF port stats, RX-packets and TX-packets are 0

Set mac forward, enable print out

Send 100 packets from tester

Check VF port stats, RX-packets and TX-packets are 100

Clear VF port stats

Check VF port stats, RX-packets and TX-packets are 0

Test case: VF information
=========================

Start testpmd

Show VF port information, check link, speed...information correctness::

    testpmd> show port info all

Set mac forward, enable print out

Send 100 packets from tester

Check VF port stats, RX-packets and TX-packets are 100


Test case: VF RX interrupt
==========================
Build l3fwd-power

Create one VF from kernel PF0, create on VF from kernel PF1::

    echo 1 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    echo 1 > /sys/bus/pci/devices/0000\:18\:00.1/sriov_numvfs

Bind VFs to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:11.0

Start l3fwd power with one queue per port::

    ./<build_target>/examples/dpdk-l3fwd-power -l 6,7 -n 4 -- \
    -p 0x3 --config '(0,0,6),(1,0,7)'

Send one packet to VF0 and VF1, check that thread on core6 and core7 waked up::

    L3FWD_POWER: lcore 6 is waked up from rx interrupt on port 0 queue 0
    L3FWD_POWER: lcore 7 is waked up from rx interrupt on port 0 queue 0

Check the packet has been normally forwarded.

After the packet forwarded, thread on core6 and core 7 will return to sleep::

    L3FWD_POWER: lcore 6 sleeps until interrupt triggers
    L3FWD_POWER: lcore 7 sleeps until interrupt triggers

Send packet flows to VF0 and VF1, check that thread on core6 and core7 will
keep up awake.

Test case: IAVF DUAL VLAN filtering
===================================

1. enable vlan filtering on port VF::

    testpmd> set fwd mac
    Set mac packet forwarding mode
    testpmd> vlan set filter on 0

2. check the vlan mode is set successfully::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    ......
    VLAN offload:
    strip off, filter on, extend off, qinq strip off

3. tester send qinq pkt and single vlan pkt which outer vlan id is 1 to VF::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

4. check the pkts can't be received in VF.

5. add rx_vlan in VF::

    testpmd> rx_vlan add 1 0

6. repeat step 3, check the pkts can be received by VF and fwd to tester::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=522 - nb_segs=1 - hw ptype: L2_ETHER  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN  - l2_len=18 - inner_l2_len=4 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - hw ptype: L2_ETHER  - sw ptype: L2_ETHER_VLAN  - l2_len=18 - Receive queue=0x0
    ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    tcpdump -i ens786f0 -nn -e -v

    16:50:38.807158 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype 0x0800,
    16:50:38.807217 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype 0x0800,

    16:51:06.083084 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype 0x0800,
    16:51:06.083127 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype 0x0800,

7. tester send qinq pkt and single vlan pkt which outer vlan id is 11 to VF::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=11,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=11,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

8. check the pkts can not be received by VF.

9. remove rx_vlan in VF1::

    testpmd> rx_vlan rm 1 0

10. repeat step 3, check the pkts can not be received by VF.


Test case: IAVF DUAL VLAN header stripping
==========================================

1. enable vlan filtering on port VF::

    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0

2. check the vlan mode is set successfully::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    ......
    VLAN offload:
    strip off, filter on, extend off, qinq strip off

3. enable vlan header stripping on VF::

    testpmd> vlan set strip on 0

4. check the vlan mode is set successfully::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    ......
    VLAN offload:
    strip on, filter on, extend off, qinq strip off

5. tester send qinq pkt and single vlan pkt which outer vlan id is 1 to VF::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

6. check the pkts can be received in VF and fwd to tester without outer vlan header::

    testpmd> port 0/queue 10: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - RSS hash=0xc7b627aa - RSS queue=0xa - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Tail/CRC: 0x58585858/0x00000000 - Receive queue=0xa
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 0/queue 10: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0xc7b627aa - RSS queue=0xa - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Tail/CRC: 0x58585858/0x00000000 - Receive queue=0xa
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    10:12:38.034948 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:12:38.035025 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 518: vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    10:12:44.806825 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:12:44.806865 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

7. disable vlan header stripping on VF1::

    testpmd> vlan set strip off 0

8. check the vlan mode is set successfully::

    testpmd> show port info 0

    ********************* Infos for port 0  *********************
    ......
    VLAN offload:
    strip off, filter on, extend off, qinq strip off

9. repeat step 5, check the pkts can be received in VF and fwd to tester with outer vlan header::

    testpmd> port 0/queue 10: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=522 - nb_segs=1 - RSS hash=0xc7b627aa - RSS queue=0xa - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Tail/CRC: 0x58585858/0x00000000 - Receive queue=0xa
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 0/queue 10: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - RSS hash=0xc7b627aa - RSS queue=0xa - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Tail/CRC: 0x58585858/0x00000000 - Receive queue=0xa
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    09:49:08.295172 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    09:49:08.295239 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    09:49:41.043101 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    09:49:41.043166 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

Test case: IAVF DUAL VLAN header insertion
==========================================

1. enable vlan filtering on port VF::

    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 11 0

2. set up test environment again::

    echo 1 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    ip link set ens785f0 vf 0 mac 00:11:22:33:44:11
    ip link set dev ens785f0 vf 0 spoofchk off
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0 -- -i --rxq=16 --txq=16
    testpmd> set fwd mac
    testpmd> set verbose 1

3. enable vlan header insertion on VF::

    testpmd> port stop 0
    Stopping ports...
    Checking link statuses...
    Done
    testpmd> tx_vlan set 0 1
    testpmd> port start 0

4. tester send pkt to VF::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=11,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

5. check the pkts with vlan header can be received in tester::

    testpmd> port 0/queue 13: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0xcaf4abfd - RSS queue=0xd - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0xd
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 0/queue 8: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - RSS hash=0x28099b78 - RSS queue=0x8 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x8
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    10:32:55.566801 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:32:55.566856 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 518: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    06:29:32.281896 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 11, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    06:29:32.281940 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 11, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

6. disable vlan header insertion on VF1::

    testpmd> port stop 0
    Stopping ports...
    Checking link statuses...
    Done
    testpmd> tx_vlan reset 0
    testpmd> port start 0

7. repeat step 4, check the pkts without vlan tag can be received in tester::

    testpmd> port 0/queue 9: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0xa63e8869 - RSS queue=0x9 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x9
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    port 0/queue 12: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - RSS hash=0x6f5533bc - RSS queue=0xc - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0xc
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    10:34:40.070754 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    10:34:40.070824 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 514: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

    06:36:57.641871 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 518: vlan 11, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    06:36:57.641909 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 518: vlan 11, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480


Test case: Enable/disable AVF CRC stripping
===========================================

1. start testpmd with "--disable-crc-strip"::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 20-23 -n 4 -a 0000:18:01.0 -- -i --rxq=16 --txq=16 --disable-crc-strip
    testpmd> set fwd mac
    testpmd> set verbose 1

2. send pkts to VF::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

3. check VF1 receive this pkts with CRC::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x890d9a70 - RSS queue=0x0 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  518
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  514

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################
    clear port stats all

4. enable crc strip in testpmd::

    testpmd> stop
    testpmd> port stop 0
    testpmd> port config 0 rx_offload keep_crc off
    testpmd> port start 0
    testpmd> start

5. repeat step 2, check VF receive this pkts without CRC::

    testpmd> port 0/queue 2: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0xa94c21d2 - RSS queue=0x2 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x2
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  514
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  514

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################
    clear port stats all

6. disable crc strip in testpmd::

    testpmd> stop
    testpmd> port stop 0
    testpmd> port config 0 rx_offload keep_crc on
    testpmd> port start 0
    testpmd> start

7. repeat step 2, check VF1 receive this pkts with CRC::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x79c10190 - RSS queue=0x0 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  518
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  514

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################
    clear port stats all

8. re-launch testpmd without "--disable-crc-strip"::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 20-23 -n 4 -a 0000:18:01.0 -- -i --rxq=16 --txq=16
    testpmd> set fwd mac
    testpmd> set verbose 1

9. repeat step 2, check VF receive this pkts without CRC::

    testpmd> port 0/queue 2: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x0800 - length=514 - nb_segs=1 - RSS hash=0x898ada82 - RSS queue=0x2 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x2
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  514
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  514

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################


Test case: IAVF CRC strip and Vlan strip co-exists
==================================================

1. start testpmd with crc strip enable, vlan strip disable::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 20-23 -n 4 -a 0000:18:01.0 -- -i --rxq=16 --txq=16
    testpmd> set fwd mac
    testpmd> set verbose 1
    testpmd> show port info 0
    ********************* Infos for port 0  *********************
    MAC address: 00:11:22:33:44:11
    Device name: 0000:18:01.1
    Driver name: net_iavf
    ......
    VLAN offload:
      strip off, filter off, extend off, qinq strip off

2. request disable vlan strip::

    testpmd> vlan set strip off 0

3. check the vlan strip still disable::

    testpmd> show port info 0
    ********************* Infos for port 0  *********************
    MAC address: 00:11:22:33:44:11
    Device name: 0000:18:01.1
    Driver name: net_iavf
    ......
    VLAN offload:
      strip off, filter off, extend off, qinq strip off

4. set vlan filter on and add rx_vlan 1::

    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> start

5. send qinq pkts to check vlan strip is off, crc strip is on::

    sendp([Ether(dst="00:11:22:33:44:11",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)], iface="ens786f0")

    testpmd> port 0/queue 6: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=522 - nb_segs=1 - RSS hash=0xf6521426 - RSS queue=0x6 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Tail/CRC: 0x58585858/0x00000000 - Receive queue=0x6
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  522
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  522

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################

    09:07:45.863251 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    09:07:45.863340 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

6. request enable vlan strip::

    testpmd> vlan set strip on 0

7. check the vlan strip enable successfully::

    testpmd> show port info 0
    ********************* Infos for port 0  *********************
    MAC address: 00:11:22:33:44:11
    Device name: 0000:18:01.1
    Driver name: net_iavf
    ......
    VLAN offload:
      strip on, filter off, extend off, qinq strip off

8. repeat step 5, send qinq pkts to check vlan strip is on(tx-4), crc strip is on::

    testpmd> port 0/queue 6: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - RSS hash=0xf6521426 - RSS queue=0x6 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Tail/CRC: 0x58585858/0x00000000 - Receive queue=0x6
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 1          RX-missed: 0          RX-bytes:  522
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 1          TX-errors: 0          TX-bytes:  518

    Throughput (since last show)
    Rx-pps:            0          Rx-bps:            0
    Tx-pps:            0          Tx-bps:            0
    ############################################################################

    11:09:03.918907 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480
    11:09:03.918952 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 518: vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
    196.222.232.221 > 127.0.0.1:  ip-proto-0 480

9. request disable vlan strip::

    testpmd> vlan set strip off 0

10. check the vlan strip disable successfully::

     testpmd> show port info 0
     ********************* Infos for port 0  *********************
     MAC address: 00:11:22:33:44:11
     Device name: 0000:18:01.1
     Driver name: net_iavf
     ......
     VLAN offload:
       strip off, filter on, extend off, qinq strip off

11. request disable crc strip::

     testpmd> stop
     testpmd> port stop 0
     testpmd> port config 0 rx_offload keep_crc on
     testpmd> port start 0
     testpmd> start

12. repeat step 5, send qinq pkts to check vlan strip is off, crc strip is off(rx+4)::

     testpmd> port 0/queue 7: received 1 packets
     src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=522 - nb_segs=1 - RSS hash=0xbc8b1857 - RSS queue=0x7 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Tail/CRC: 0x58585858/0x6d870bf6 - Receive queue=0x7
     ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

     show port stats all
     ######################## NIC statistics for port 0  ########################
     RX-packets: 1          RX-missed: 0          RX-bytes:  526
     RX-errors: 0
     RX-nombuf:  0
     TX-packets: 1          TX-errors: 0          TX-bytes:  522

     Throughput (since last show)
     Rx-pps:            0          Rx-bps:            0
     Tx-pps:            0          Tx-bps:            0
     ############################################################################

     10:23:57.350934 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480
     10:23:57.351008 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480

13. request enable vlan strip::

     testpmd> vlan set strip on 0
     iavf_execute_vf_cmd(): No response or return failure (-64) for cmd 54
     iavf_config_vlan_strip_v2(): fail to execute command VIRTCHNL_OP_ENABLE_VLAN_STRIPPING_V2
     rx_vlan_strip_set(port_pi=0, on=1) failed diag=-5

14. repeat step 5, send qinq pkts to check the vlan strip can not enable::

     testpmd> port 0/queue 7: received 1 packets
     src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=518 - nb_segs=1 - RSS hash=0xbc8b1857 - RSS queue=0x7 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Tail/CRC: 0x58585858/0x6d870bf6 - Receive queue=0x7
     ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

     show port stats all
     ######################## NIC statistics for port 0  ########################
     RX-packets: 1          RX-missed: 0          RX-bytes:  526
     RX-errors: 0
     RX-nombuf:  0
     TX-packets: 1          TX-errors: 0          TX-bytes:  522

     Throughput (since last show)
     Rx-pps:            0          Rx-bps:            0
     Tx-pps:            0          Tx-bps:            0
     ############################################################################

     10:26:08.346936 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480
     10:26:08.347006 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480

15. request disable vlan strip::

     vlan set strip off 0

16. check the vlan strip still disable::

     testpmd> show port info 0
     ********************* Infos for port 0  *********************
     MAC address: 00:11:22:33:44:11
     Device name: 0000:18:01.1
     Driver name: net_iavf
     ......
     VLAN offload:
       strip off, filter on, extend off, qinq strip off

17. request enable crc strip::

     testpmd> stop
     testpmd> port stop 0
     testpmd> port config 0 rx_offload keep_crc off
     testpmd> port start 0
     testpmd> start

18. repeat step 5, send qinq pkts to check the crc strip enable successfully::

     testpmd> port 0/queue 3: received 1 packets
     src=00:00:00:00:00:00 - dst=00:11:22:33:44:11 - type=0x8100 - length=522 - nb_segs=1 - RSS hash=0x2b4ad203 - RSS queue=0x3 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Receive queue=0x3
     ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
     port 0/queue 3: sent 1 packets
     src=00:11:22:33:44:11 - dst=02:00:00:00:00:00 - type=0x8100 - length=522 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Send queue=0x3
     ol_flags: PKT_RX_L4_CKSUM_UNKNOWN PKT_RX_IP_CKSUM_UNKNOWN PKT_RX_OUTER_L4_CKSUM_UNKNOWN

     show port stats all
     ######################## NIC statistics for port 0  ########################
     RX-packets: 1          RX-missed: 0          RX-bytes:  522
     RX-errors: 0
     RX-nombuf:  0
     TX-packets: 1          TX-errors: 0          TX-bytes:  522

     Throughput (since last show)
     Rx-pps:            0          Rx-bps:            0
     Tx-pps:            0          Tx-bps:            0
     ############################################################################

     10:29:19.995352 00:00:00:00:00:00 > 00:11:22:33:44:11, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480
     10:29:19.995424 00:11:22:33:44:11 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype 802.1Q, vlan 2, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto Options (0), length 500)
     196.222.232.221 > 127.0.0.1:  ip-proto-0 480

