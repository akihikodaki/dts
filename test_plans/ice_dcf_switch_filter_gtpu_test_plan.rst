.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021 Intel Corporation

================================
ICE DCF Switch Filter GTPU Tests
================================

Description
===========

This document provides the plan for testing DCF switch filter gtpu of Intel® Ethernet 800 Series, including:

* Enable DCF switch filter for GTPU, the Pattern and Input Set are shown in the below table

Pattern and input set
---------------------

  +---------------------+-------------------------------+------------------------------------------------------+
  |    Packet Types     |           Pattern             |                Input Set                             |
  +=====================+===============================+======================================================+
  |                     |  MAC_IPV4_GTPU                |   [TEID], outer: l3[dst] [src]                       |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU                |   [TEID], outer: l3dst] [src]                        |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV4_GTPU_IPV4           |   [TEID], inner: l3[dst] [src]                       |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV4_GTPU_IPV4_TCP       |   [TEID], inner: l3[dst] [src] l4[dst] [src]         |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV4_GTPU_IPV4_UDP       |   [TEID], inner: l3[dst] [src] l4[dst] [src]         |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV4_GTPU_IPV6           |   [TEID], inner: l3[dst] [src]                       |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV4_GTPU_IPV6_TCP       |   [TEID], inner: l3[dst] [src] l4[dst] [src]         |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV4_GTPU_IPV6_UDP       |   [TEID], inner: l3[dst] [src] l4[dst] [src]         |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU_IPV4           |   [TEID], inner: l3[dst] [src]                       |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU_IPV4_TCP       |   [TEID], inner: l3[dst] [src] l4[dst] [src]         |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU_IPV4_UDP       |   [TEID], inner: l3[dst] [src] l4[dst] [src]         |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU_IPV6           |   [TEID], inner: l3[dst] [src]                       |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU_IPV6_TCP       |   [TEID], inner: l3[dst] [src] l4[dst] [src]         |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU_IPV6_UDP       |   [TEID], inner: l3[dst] [src] l4[dst] [src]         |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV4_GTPU_EH_IPV4        |   [QFI] [TEID], inner: l3[dst] [src]                 |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV4_GTPU_EH_IPV4_TCP    |   [QFI] [TEID], inner: l3[dst] [src] l4[dst] [src]   |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV4_GTPU_EH_IPV4_UDP    |   [QFI] [TEID], inner: l3[dst] [src] l4[dst] [src]   |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV4_GTPU_EH_IPV6        |   [QFI] [TEID], inner: l3[dst] [src]                 |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV4_GTPU_EH_IPV6_TCP    |   [QFI] [TEID], inner: l3[dst] [src] l4[dst] [src]   |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV4_GTPU_EH_IPV6_UDP    |   [QFI] [TEID], inner: l3[dst] [src] l4[dst] [src]   |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU_EH_IPV4        |   [QFI] [TEID], inner: l3[dst] [src]                 |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU_EH_IPV4_TCP    |   [QFI] [TEID], inner: l3[dst] [src] l4[dst] [src]   |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU_EH_IPV4_UDP    |   [QFI] [TEID], inner: l3[dst] [src] l4[dst] [src]   |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU_EH_IPV6        |   [QFI] [TEID], inner: l3[dst] [src]                 |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU_EH_IPV6_TCP    |   [QFI] [TEID], inner: l3[dst] [src] l4[dst] [src]   |
  +---------------------+-------------------------------+------------------------------------------------------+
  |                     |  MAC_IPV6_GTPU_EH_IPV6_UDP    |   [QFI] [TEID], inner: l3[dst] [src] l4[dst] [src]   |
  +---------------------+-------------------------------+------------------------------------------------------+

.. note::

   1. The maximum input set length of a switch rule is 32 bytes, and src ipv6,
      dst ipv6 account for 32 bytes. Therefore, for ipv6 cases, if need to test
      fields other than src, dst ip, we create rule by removing src or dst ip in
      the test plan.


Supported action type
---------------------

* To vf/vsi


Prerequisites
=============

1. Hardware:
   Intel® Ethernet 810 Series: E810-XXVDA4/E810-CQ

2. Software::

      dpdk: http://dpdk.org/git/dpdk
      scapy: http://www.secdev.org/projects/scapy/

3. Copy specific ice package to /lib/firmware/updates/intel/ice/ddp/ice.pkg,
   then load driver::

     rmmod ice
     insmod ice.ko

4. Compile DPDK::

     CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static x86_64-native-linuxapp-gcc
     ninja -C x86_64-native-linuxapp-gcc

5. Get the pci device id of DUT, for example::

     ./usertools/dpdk-devbind.py -s

     0000:18:00.0 'Device 1593' if=enp24s0f0 drv=ice unused=vfio-pci
     0000:18:00.1 'Device 1593' if=enp24s0f1 drv=ice unused=vfio-pci

6. Generate 2 VFs on PF0::

     echo 2 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

     ./usertools/dpdk-devbind.py -s
     0000:18:01.0 'Ethernet Adaptive Virtual Function 1889' if=enp24s1 drv=iavf unused=vfio-pci
     0000:18:01.1 'Ethernet Adaptive Virtual Function 1889' if=enp24s1f1 drv=iavf unused=vfio-pci

7. Set VF0 as trust::

     ip link set enp24s0f0 vf 0 trust on

8. Bind VFs to dpdk driver::

     modprobe vfio-pci
     ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0 0000:18:01.1

9. Launch dpdk on VF0 and VF1, and VF0 request DCF mode::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf,representor=[1] -a 0000:18:01.1 -- -i
     testpmd> set portlist 2
     testpmd> set fwd rxonly
     testpmd> set verbose 1
     testpmd> start
     testpmd> show port info all

   check the VF0 driver is net_ice_dcf.

Test step:
==========

* validate rule
* create rule
* send matched pkts and mismatched pkts
* destroy rule
* send matched pkts
* flush rule


take 'MAC_IPV4_GTPU_TEID_with_mask' for example:

1.validate and create rule::

   flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / end actions represented_port ethdev_port_id 1 / end
   Flow rule validated
   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / end actions represented_port ethdev_port_id 1 / end
   Flow rule #0 created

2.send 2 matched pkts and check port 2 received 2 pkts::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(teid=0x12345678)/Raw("x" *20)
   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(teid=0x12345688)/Raw("x" *20)

   ---------------------- Forward statistics for port 2  ----------------------
   RX-packets: 2              RX-dropped: 0             RX-total: 2
   TX-packets: 0              TX-dropped: 0             TX-total: 0
   ----------------------------------------------------------------------------

   +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
   RX-packets: 2              RX-dropped: 0             RX-total: 2
   TX-packets: 0              TX-dropped: 0             TX-total: 0
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

3.send 1 mismatched pkts and check port 2 not received pkts::

   p = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(teid=0x12345677)/Raw("x" *20)

   ---------------------- Forward statistics for port 2  ----------------------
   RX-packets: 0              RX-dropped: 0             RX-total: 0
   TX-packets: 0              TX-dropped: 0             TX-total: 0
   ----------------------------------------------------------------------------

   +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
   RX-packets: 0              RX-dropped: 0             RX-total: 0
   TX-packets: 0              TX-dropped: 0             TX-total: 0
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

4.destory rule and re-send step 2 matched pkts check port 2 not received pkts::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(teid=0x12345678)/Raw("x" *20)
   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(teid=0x12345688)/Raw("x" *20)

   ---------------------- Forward statistics for port 2  ----------------------
   RX-packets: 0              RX-dropped: 0             RX-total: 0
   TX-packets: 0              TX-dropped: 0             TX-total: 0
   ----------------------------------------------------------------------------

   +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
   RX-packets: 0              RX-dropped: 0             RX-total: 0
   TX-packets: 0              TX-dropped: 0             TX-total: 0
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


Pattern: MAC_IPV4_GTPU
----------------------

Test case: MAC_IPV4_GTPU
>>>>>>>>>>>>>>>>>>>>>>>>

subcase 1: MAC_IPV4_GTPU_TEID_with_mask
:::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(teid=0x12345678)/Raw("x" *20)
   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(teid=0x12345688)/Raw("x" *20)

mismatched packets::

   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(teid=0x12345677)/Raw("x" *20)

subcase 2: MAC_IPV4_GTPU_TEID_without_mask
::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(teid=0x12345678)/Raw("x" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(teid=0x12345688)/Raw("x" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(teid=0x12345677)/Raw("x" *20)

subcase 3: MAC_IPV4_GTPU_dst
::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 dst is 192.168.1.2 / udp / gtpu / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.2")/UDP()/GTP_U_Header()/Raw("x" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.22")/UDP()/GTP_U_Header()/Raw("x" *20)

subcase 4: MAC_IPV4_GTPU_src
::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 / udp / gtpu / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1")/UDP()/GTP_U_Header()/Raw("x" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.11")/UDP()/GTP_U_Header()/Raw("x" *20)

subcase 5: MAC_IPV4_GTPU_src_dst
::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / gtpu / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.2")/UDP()/GTP_U_Header()/Raw("x" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.11", dst="192.168.1.2")/UDP()/GTP_U_Header()/Raw("x" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.22")/UDP()/GTP_U_Header()/Raw("x" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.11", dst="192.168.1.22")/UDP()/GTP_U_Header()/Raw("x" *20)

subcase 6: MAC_IPV4_GTPU_teid_dst
:::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 dst is 192.168.1.2 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.2")/UDP()/GTP_U_Header(teid=0x12345678)/Raw("x" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.22")/UDP()/GTP_U_Header(teid=0x12345678)/Raw("x" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.2")/UDP()/GTP_U_Header(teid=0x12345677)/Raw("x" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.22")/UDP()/GTP_U_Header(teid=0x12345677)/Raw("x" *20)

subcase 7: MAC_IPV4_GTPU_teid_src
:::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1")/UDP()/GTP_U_Header(teid=0x12345678)/Raw("x" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.11")/UDP()/GTP_U_Header(teid=0x12345678)/Raw("x" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1")/UDP()/GTP_U_Header(teid=0x12345677)/Raw("x" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.11")/UDP()/GTP_U_Header(teid=0x12345677)/Raw("x" *20)


subcase 8: MAC_IPV4_GTPU_ALL
::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.2")/UDP()/GTP_U_Header(teid=0x12345678)/Raw("x" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.11", dst="192.168.1.2")/UDP()/GTP_U_Header(teid=0x12345678)/Raw("x" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.22")/UDP()/GTP_U_Header(teid=0x12345678)/Raw("x" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.11", dst="192.168.1.22")/UDP()/GTP_U_Header(teid=0x12345678)/Raw("x" *20)
   p5 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.11", dst="192.168.1.22")/UDP()/GTP_U_Header(teid=0x12345677)/Raw("x" *20)

Pattern: MAC_IPV6_GTPU
----------------------
reconfig all the cases of "Test case: MAC_IPV4_GTPU"

    rule:
        change ipv4 to ipv6, ipv4 address to ipv6 address.
    packets:
        change the packet's L3 layer from IP to IPv6;
        change the ipv4 address to ipv6 address.

Test case: MAC_IPV6_GTPU
>>>>>>>>>>>>>>>>>>>>>>>>

subcase 1: MAC_IPV6_GTPU_TEID_with_mask
:::::::::::::::::::::::::::::::::::::::

subcase 2: MAC_IPV6_GTPU_TEID_without_mask
::::::::::::::::::::::::::::::::::::::::::

subcase 3: MAC_IPV6_GTPU_dst
::::::::::::::::::::::::::::

subcase 4: MAC_IPV6_GTPU_src
::::::::::::::::::::::::::::

subcase 5: MAC_IPV6_GTPU_src_dst
::::::::::::::::::::::::::::::::

subcase 6: MAC_IPV6_GTPU_teid_dst
:::::::::::::::::::::::::::::::::

subcase 7: MAC_IPV6_GTPU_teid_src
:::::::::::::::::::::::::::::::::

subcase 8: MAC_IPV4_GTPU_ALL
::::::::::::::::::::::::::::

Pattern: outer ipv4 + inner ipv4
--------------------------------

Test case: MAC_IPV4_GTPU_EH_IPV4
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

basic pkts:

ipv4-nonfrag packet::

   Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/("X" *20)

ipv4-frag packet::

    Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(frag=6)/("X" *20)

subcase 1: MAC_IPV4_GTPU_EH_IPV4_TEID_with_mask
:::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1: send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345678)
   pkts_set2: send pkts_set1 with teid 0x12345688

mismatched packets::

   pkts_set3: send pkts_set1 with teid 0x12345677

subcase 2: MAC_IPV4_GTPU_EH_IPV4_TEID_without_mask
::::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / ipv4 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345678)

mismatched packets::

   pkts_set2: send pkts_set1 with teid 0x12345677
   pkts_set3: send pkts_set1 with teid 0x12345688

subcase 3: MAC_IPV4_GTPU_EH_IPV4_QFI
::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1: send basic pkts with GTPPDUSessionContainer(QFI=0x34)

mismatched packets::

   pkts_set2: send basic pkts with qfi 0x33

subcase 4: MAC_IPV4_GTPU_EH_IPV4_L3DST
::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.1.2 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1: send basic pkts with inner l3dst, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(dst="192.168.1.2")/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3dst, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(dst="192.168.1.22")/("X" *20)

subcase 5: MAC_IPV4_GTPU_EH_IPV4_L3SRC
::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1: send basic pkts with inner l3src, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1")/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11")/("X" *20)

subcase 6: MAC_IPV4_GTPU_EH_IPV4_L3SRC_L3DST
::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1: send basic pkts with inner l3src l3dst, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src l3dst, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.2")/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.22")/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")/("X" *20)

subcase 7: MAC_IPV4_GTPU_EH_IPV4_TEID_L3SRC_L3DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu  teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1: send basic pkts with inner l3src l3dst, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src l3dst, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.21")/("X" *20)

subcase 8: MAC_IPV4_GTPU_EH_IPV4_QFI_L3SRC_L3DST
::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1: send basic pkts with inner l3src l3dst, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src l3dst, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.11", dst="192.168.1.22")/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.1", dst="192.168.1.2")/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.11", dst="192.168.1.22")/("X" *20)


subcase 9: MAC_IPV4_GTPU_EH_IPV4_ALL
::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu  teid is 0x12345678 teid mask 0x00000001 / gtp_psc qfi is 0x34 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1: take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")/("X" *20)

mismatched packets::

   pkts_set2: take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.11", dst="192.168.1.22")/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.1", dst="192.168.1.2")/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.11", dst="192.168.1.22")/("X" *20)

Test case: MAC_IPV4_GTPU_EH_IPV4_UDP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

basic pkts::

   Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP()/("X" *20)

subcase 1: MAC_IPV4_GTPU_EH_IPV4_UDP_TEID_with_mask
:::::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP()/UDP()/("X" *20)
   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345688)/GTPPDUSessionContainer()/IP()/UDP()/("X" *20)

mismatched packets::

   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/GTPPDUSessionContainer()/IP()/UDP()/("X" *20)

subcase 2: MAC_IPV4_GTPU_EH_IPV4_UDP_TEID_without_mask
::::::::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / ipv4 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP()/UDP()/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345688)/GTPPDUSessionContainer()/IP()/UDP()/("X" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/GTPPDUSessionContainer()/IP()/UDP()/("X" *20)

subcase 3: MAC_IPV4_GTPU_EH_IPV4_UDP_QFI
::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x34)/IP()/UDP()/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x33)/IP()/UDP()/("X" *20)

subcase 4: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST
::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.1.2 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(dst="192.168.1.2")/UDP()/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(dst="192.168.1.22")/UDP()/("X" *20)

subcase 5: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC
::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP()/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11")/UDP()/("X" *20)

subcase 6: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC_L3DST
::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP()/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.2")/UDP()/("X" *20)
   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.22")/UDP()/("X" *20)
   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")/UDP()/("X" *20)

subcase 7: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / udp dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP(dport=23)/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11")/UDP(dport=23)/("X" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP(dport=13)/("X" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11")/UDP(dport=13)/("X" *20)

subcase 8: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / udp src is 22 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP(sport=22)/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11")/UDP(sport=22)/("X" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP(sport=12)/("X" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11")/UDP(sport=12)/("X" *20)


subcase 9: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.1.2 / udp src is 22 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(dst="192.168.1.2")/UDP(sport=22)/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(dst="192.168.1.22")/UDP(sport=22)/("X" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(dst="192.168.1.2")/UDP(sport=12)/("X" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(dst="192.168.1.22")/UDP(sport=12)/("X" *20)

subcase 10: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.1.2 / udp dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(dst="192.168.1.2")/UDP(dport=23)/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(dst="192.168.1.22")/UDP(dport=23)/("X" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(dst="192.168.1.2")/UDP(dport=13)/("X" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(dst="192.168.1.22")/UDP(dport=13)/("X" *20)

subcase 11: MAC_IPV4_GTPU_EH_IPV4_UDP_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP(dport=23)/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP(dport=13)/("X" *20)

subcase 12: MAC_IPV4_GTPU_EH_IPV4_UDP_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp src is 22 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP(sport=22)/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP(sport=12)/("X" *20)

subcase 13: MAC_IPV4_GTPU_EH_IPV4_UDP_L4SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp src is 22 dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP(sport=22, dport=23)/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP(sport=12, dport=23)/("X" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP(sport=22, dport=13)/("X" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP(sport=12, dport=13)/("X" *20)

subcase 14: MAC_IPV4_GTPU_EH_IPV4_UDP_TEID_L3SRC_L3DST
::::::::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP()/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")/UDP()/("X" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP()/("X" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")/UDP()/("X" *20)

subcase 15: MAC_IPV4_GTPU_EH_IPV4_UDP_QFI_L3SRC_L3DST
:::::::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP()/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.11", dst="192.168.1.22")/UDP()/("X" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP()/("X" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.11", dst="192.168.1.22")/UDP()/("X" *20)

subcase 16: MAC_IPV4_GTPU_EH_IPV4_UDP_TEID_L4SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 / udp src is 22 dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP()/UDP(sport=22, dport=23)/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP()/UDP(sport=12, dport=13)/("X" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/GTPPDUSessionContainer()/IP()/UDP(sport=22, dport=23)/("X" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/GTPPDUSessionContainer()/IP()/UDP(sport=12, dport=13)/("X" *20)

subcase 17: MAC_IPV4_GTPU_EH_IPV4_UDP_QFI_L4SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 / udp src is 22 dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x34)/IP()/UDP(sport=22, dport=23)/("X" *20)

mismatched packets::

   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x34)/IP()/UDP(sport=12, dport=13)/("X" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x33)/IP()/UDP(sport=22, dport=23)/("X" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(QFI=0x33)/IP()/UDP(sport=12, dport=13)/("X" *20)

subcase 18: MAC_IPV4_GTPU_EH_IPV4_UDP_L3_l4
:::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 22 dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=22, dport=23)/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=12, dport=23)/("X" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=22, dport=13)/("X" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=12, dport=13)/("X" *20)
   p5 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.2")/UDP(sport=22, dport=23)/("X" *20)
   p6 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.22")/UDP(sport=22, dport=23)/("X" *20)
   p7 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")/UDP(sport=22, dport=23)/("X" *20)
   p8 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")/UDP(sport=12, dport=13)/("X" *20)

subcase 19: MAC_IPV4_GTPU_EH_IPV4_UDP_ALL
:::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc qfi is 0x34 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 22 dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   p1 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")/udp(sport=22, dport=23)/("X" *20)

mismatched packets::

   p2 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")/udp(sport=22, dport=23)/("X" *20)
   p3 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.1", dst="192.168.1.2")/udp(sport=22, dport=23)/("X" *20)
   p4 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.11", dst="192.168.1.22")/udp(sport=22, dport=23)/("X" *20)
   p5 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")/udp(sport=12, dport=13)/("X" *20)
   p6 = Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.11", dst="192.168.1.22")/udp(sport=12, dport=13)/("X" *20)

Test case: MAC_IPV4_GTPU_EH_IPV4_TCP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

reconfig all case of 'Test case: MAC_IPV4_GTPU_EH_IPV4_UDP':
   rule and pkts:
      change inner 'udp' to 'tcp'

subcase 1: MAC_IPV4_GTPU_EH_IPV4_TCP_TEID_with_mask
:::::::::::::::::::::::::::::::::::::::::::::::::::

subcase 2: MAC_IPV4_GTPU_EH_IPV4_TCP_TEID_without_mask
::::::::::::::::::::::::::::::::::::::::::::::::::::::

subcase 3: MAC_IPV4_GTPU_EH_IPV4_TCP_QFI
::::::::::::::::::::::::::::::::::::::::

subcase 4: MAC_IPV4_GTPU_EH_IPV4_TCP_L3DST
::::::::::::::::::::::::::::::::::::::::::

subcase 5: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRC
::::::::::::::::::::::::::::::::::::::::::

subcase 6: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRC_L3DST
::::::::::::::::::::::::::::::::::::::::::::::::

subcase 7: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::::

subcase 8: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRC_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::::

subcase 9: MAC_IPV4_GTPU_EH_IPV4_TCP_L3DST_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::::

subcase 10: MAC_IPV4_GTPU_EH_IPV4_TCP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::

subcase 11: MAC_IPV4_GTPU_EH_IPV4_TCP_L4DST
:::::::::::::::::::::::::::::::::::::::::::

subcase 12: MAC_IPV4_GTPU_EH_IPV4_TCP_L4SRC
:::::::::::::::::::::::::::::::::::::::::::

subcase 13: MAC_IPV4_GTPU_EH_IPV4_TCP_L4SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::

subcase 14: MAC_IPV4_GTPU_EH_IPV4_TCP_TEID_L3SRC_L3DST
::::::::::::::::::::::::::::::::::::::::::::::::::::::

subcase 15: MAC_IPV4_GTPU_EH_IPV4_TCP_QFI_L3SRC_L3DST
:::::::::::::::::::::::::::::::::::::::::::::::::::::

subcase 16: MAC_IPV4_GTPU_EH_IPV4_TCP_TEID_L4SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::::::::::

subcase 17: MAC_IPV4_GTPU_EH_IPV4_TCP_QFI_L4SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::::::

subcase 18: MAC_IPV4_GTPU_EH_IPV4_TCP_L3_l4
:::::::::::::::::::::::::::::::::::::::::::

subcase 19: MAC_IPV4_GTPU_EH_IPV4_TCP_ALL
:::::::::::::::::::::::::::::::::::::::::

Test case: MAC_IPV4_GTPU_IPV4
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

basic pkts:
ipv4-nonfrag packet::

   Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/("X" *20)

ipv4-frag packet::

    Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(frag=6)/("X" *20)

subcase 1: MAC_IPV4_GTPU_IPV4_TEID_with_mask
::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345678)

   pkts_set2:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345688)

mismatched packets::

   pkts_set3:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345677)

subcase 2: MAC_IPV4_GTPU_IPV4_TEID_without_mask
:::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / ipv4 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345678)

mismatched packets::

   pkts_set2:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345688)

   pkts_set3:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345677)

subcase 3: MAC_IPV4_GTPU_IPV4_L3DST
:::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.1.2 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3dst, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(dst="192.168.1.2")/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3dst:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(dst="192.168.1.22")/("X" *20)

subcase 4: MAC_IPV4_GTPU_IPV4_L3SRC
:::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3src, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.1")/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.11")/("X" *20)

subcase 4: MAC_IPV4_GTPU_IPV4_L3SRC_L3DST
:::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3src l4dst, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.1" dst="192.168.1.2")/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src l4dst:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.2")/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.22")/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.22")/("X" *20)

subcase 5: MAC_IPV4_GTPU_IPV4_ALL
:::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3src l4dst, take 'ipv4-nonfrag' for example:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.1" dst="192.168.1.2")/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.11", dst="192.168.1.22")/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/IP(src="192.168.1.11", dst="192.168.1.22")/("X" *20)

Test case: MAC_IPV4_GTPU_IPV4_UDP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

basic pkts::

    Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP()/("X" *20)

subcase 1: MAC_IPV4_GTPU_IPV4_UDP_TEID_with_mask
::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345678)

   pkts_set2:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345688)

mismatched packets::

   pkts_set3:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345677)

subcase 2: MAC_IPV4_GTPU_IPV4_UDP_TEID_without_mask
:::::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / ipv4 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345678)

mismatched packets::

   pkts_set2:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345688)

   pkts_set3:send basic pkts with GTP_U_Header(gtp_type=255, teid=0x12345677)


subcase 3: MAC_IPV4_GTPU_IPV4_UDP_L3DST
:::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.1.2 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(dst="192.168.1.2")/UDP()/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3dst:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(dst="192.168.1.22")/UDP()/("X" *20)

subcase 4: MAC_IPV4_GTPU_IPV4_UDP_L3SRC
:::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3src
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.1")/UDP()/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src:
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.11")/UDP()/("X" *20)

subcase 5: MAC_IPV4_GTPU_IPV4_UDP_L3SRC_L3DST
:::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3src l3dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.1" dst="192.168.1.2")/UDP()/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src l3dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.2")/UDP()/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.22")/UDP()/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.22")/UDP()/("X" *20)

subcase 6: MAC_IPV4_GTPU_IPV4_UDP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 / udp dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3src l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.1")/UDP(dport=23)/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.11")/UDP(dport=23)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.1")/UDP(dport=13)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.11")/UDP(dport=13)/("X" *20)

subcase 7: MAC_IPV4_GTPU_IPV4_UDP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 / udp src is 22 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3src l4src
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.1")/UDP(sport=22)/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src l4src
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.11")/UDP(sport=22)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.1")/UDP(sport=12)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.11")/UDP(sport=12)/("X" *20)

subcase 8: MAC_IPV4_GTPU_IPV4_UDP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.1.2 / udp src is 22 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3dst l4src
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(dst="192.168.1.2")/UDP(sport=22)/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3dst l4src
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(dst="192.168.1.12")/UDP(sport=22)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(dst="192.168.1.2")/UDP(sport=12)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(dst="192.168.1.12")/UDP(sport=12)/("X" *20)

subcase 9: MAC_IPV4_GTPU_IPV4_UDP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.1.2 / udp dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3dst l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(dst="192.168.1.2")/UDP(dport=23)/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3dst l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(dst="192.168.1.12")/UDP(dport=23)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(dst="192.168.1.2")/UDP(dport=13)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(dst="192.168.1.12")/UDP(dport=13)/("X" *20)

subcase 10: MAC_IPV4_GTPU_IPV4_UDP_L4DST
::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP(dport=23)/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP(dport=13)/("X" *20)

subcase 11: MAC_IPV4_GTPU_IPV4_UDP_L4SRC
::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp src is 22 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l4src
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP(sport=22)/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l4src
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP(sport=12)/("X" *20)

subcase 12: MAC_IPV4_GTPU_IPV4_UDP_L4SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp src is 22 dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l4src l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP(sport=22, dport=23)/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l4src l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP(sport=22, dport=13)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP(sport=12, dport=23)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP(sport=12, dport=13)/("X" *20)

subcase 13: MAC_IPV4_GTPU_IPV4_UDP_TIED_L3SRC_L3DST
:::::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3src l3dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.1" dst="192.168.1.2")/UDP()/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src l3dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.11", dst="192.168.1.22")/UDP()/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP()/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/IP(src="192.168.1.11", dst="192.168.1.22")/UDP()/("X" *20)


subcase 14: MAC_IPV4_GTPU_IPV4_UDP_TEID_L4SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 / udp src is 22 dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l4src l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP(sport=22, dport=23)/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l4src l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP(sport=12, dport=13)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/IP()/UDP(sport=22, dport=23)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/IP()/UDP(sport=12, dport=13)/("X" *20)


subcase 15: MAC_IPV4_GTPU_IPV4_UDP_L3_L4
::::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 22 dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3src l3dst l4src l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=22, dport=23)/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src l3dst l4src l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.22")/UDP(sport=22, dport=23)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=12, dport=13)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.22")/UDP(sport=12, dport=13)/("X" *20)

subcase 16: MAC_IPV4_GTPU_IPV4_UDP_ALL
::::::::::::::::::::::::::::::::::::::
rule::

   flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 22 dst is 23 / end actions represented_port ethdev_port_id 1 / end

matched packets::

   pkts_set1:send basic pkts with inner l3src l3dst l4src l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=22, dport=23)/("X" *20)

mismatched packets::

   pkts_set2: send pkts_set1 with different inner l3src l3dst l4src l4dst
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.11", dst="192.168.1.22")/UDP(sport=22, dport=23)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=12, dport=13)/("X" *20)
      Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header(gtp_type=255, teid=0x12345677)/IP(src="192.168.1.11", dst="192.168.1.22")/UDP(sport=12, dport=13)/("X" *20)


Test case: MAC_IPV4_GTPU_IPV4_TCP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

reconfig all case of 'Test case: MAC_IPV4_GTPU_IPV4_UDP':
   rule and pkts:
      change inner 'udp' to 'tcp'

subcase 1: MAC_IPV4_GTPU_IPV4_TCP_TEID_with_mask
::::::::::::::::::::::::::::::::::::::::::::::::

subcase 2: MAC_IPV4_GTPU_IPV4_TCP_TEID_without_mask
:::::::::::::::::::::::::::::::::::::::::::::::::::

subcase 3: MAC_IPV4_GTPU_IPV4_TCP_L3DST
:::::::::::::::::::::::::::::::::::::::

subcase 4: MAC_IPV4_GTPU_IPV4_TCP_L3SRC
:::::::::::::::::::::::::::::::::::::::

subcase 5: MAC_IPV4_GTPU_IPV4_TCP_L3SRC_L3DST
:::::::::::::::::::::::::::::::::::::::::::::

subcase 6: MAC_IPV4_GTPU_IPV4_TCP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::

subcase 7: MAC_IPV4_GTPU_IPV4_TCP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::

subcase 8: MAC_IPV4_GTPU_IPV4_TCP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::

subcase 9: MAC_IPV4_GTPU_IPV4_TCP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::

subcase 10: MAC_IPV4_GTPU_IPV4_TCP_L4DST
::::::::::::::::::::::::::::::::::::::::

subcase 11: MAC_IPV4_GTPU_IPV4_TCP_L4SRC
::::::::::::::::::::::::::::::::::::::::

subcase 12: MAC_IPV4_GTPU_IPV4_TCP_L4SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::

subcase 13: MAC_IPV4_GTPU_IPV4_TCP_TIED_L3SRC_L3DST
:::::::::::::::::::::::::::::::::::::::::::::::::::

subcase 14: MAC_IPV4_GTPU_IPV4_TCP_TEID_L4SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::::

subcase 15: MAC_IPV4_GTPU_IPV4_TCP_L3_L4
::::::::::::::::::::::::::::::::::::::::

subcase 16: MAC_IPV4_GTPU_IPV4_TCP_ALL
::::::::::::::::::::::::::::::::::::::

Pattern: outer ipv4 + inner ipv6
--------------------------------

reconfig all the cases of "Pattern: outer ipv4 + inner ipv4"

    rule:
        change inner ipv4 to ipv6
    packets:
        change the packet's inner L3 layer from IP to IPv6;
        change the ipv4 address to ipv6 address.

Pattern: outer ipv6 + inner ipv4
--------------------------------

reconfig all the cases of "Pattern: outer ipv4 + inner ipv4"

    rule:
        change outer ipv4 to ipv6.
    packets:
        change the packet's outer L3 layer from IP to IPv6;

Pattern: outer ipv6 + inner ipv6
--------------------------------

reconfig all the cases of "Pattern: outer ipv4 + inner ipv4"

    rule:
        change outer ipv4 to ipv6.
        change inner ipv4 to ipv6.
    packets:
        change the packet's outer L3 layer from IP to IPv6;
        change the packet's inner L3 layer from IP to IPv6;
        change the ipv4 address to ipv6 address.
