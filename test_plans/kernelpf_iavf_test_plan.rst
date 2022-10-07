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
ICE driver NIC.

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


Test case: VF MAC filter
========================
Disable promisc mode, add a new MAC to VF0 and then start testpmd::

    testpmd> set promisc all off
    testpmd> mac_addr add 0 00:11:22:33:44:55
    testpmd> set fwd mac
    testpmd> start

Use scapy to send 100 random packets with current VF0's MAC, verify the
packets can be received and forwarded by the VF::

    p=Ether(dst="00:01:23:45:67:89")/IP()/Raw(load='X'*30)

Use scapy to send 100 random packets with new added VF0's MAC, verify the
packets can be received and forwarded by the VF::

    p=Ether(dst="00:11:22:33:44:55")/IP()/Raw(load='X'*30)

Use scapy to send 100 random packets with a wrong MAC to VF0, verify the
packets can't be received by the VF.

Remove the MAC 00:11:22:33:44:55::

    testpmd> mac_addr remove 0 00:11:22:33:44:55

Use scapy to send 100 random packets with removed VF0's MAC, verify the
packets can't be received and forwarded by the VF::

    p=Ether(dst="00:11:22:33:44:55")/IP()/Raw(load='X'*30)

Set the default mac address to other mac, check the mac address has be changed
to new set mac::

    testpmd> mac_addr set 0 00:01:23:45:67:11
    testpmd> show port info 0

Use scapy to send 100 random packets with original VF0's MAC, verify the
packets can't be received and forwarded by the VF::

    p=Ether(dst="00:01:23:45:67:89")/IP()/Raw(load='X'*30)

Use scapy to send 100 random packets with new set VF0's MAC, verify the
packets can be received and forwarded by the VF::

    p=Ether(dst="00:01:23:45:67:11")/IP()/Raw(load='X'*30)

Reset to original mac address

Note::
    Not set VF MAC from kernel PF for this case, if set, will print
    "not permitted error" when add new MAC for VF.

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
Enable kernel trust mode::

    ip link set $PF_INTF vf 0 trust on

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

Send packet with current VF0's MAC, and check VF can receive the packet.

Send packet with multicast MAC 01:80:C2:00:00:08, and check VF can
receive the packet.

Disable kernel trust mode::

    ip link set $PF_INTF vf 0 trust off

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
