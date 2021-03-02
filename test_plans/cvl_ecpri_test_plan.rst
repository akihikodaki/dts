.. Copyright (c) <2021>, Intel Corporation
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

==========================
CVL support eCPRI protocol
==========================
eCPRI protocol is used for exchanging messages within ORAN 5G Front Haul.
According to the ORAN FH specification the eCPRI packets are sent over Ethernet.
They can be transmitted over standard Ethernet frames, or can use IP/UDP as the transport mechanism.
In case of the IP/UDP transport mechanism the ORAN FH standard says that
the UDP destination port used for eCPRI protocol is not fixed, thus, the user should be able to configure the port number dynamically.
A change is required in DPDK APIs to allow it.
And CVL rss and fdir rte_flow APIs are needed to support classfication of eCPRI protocol.
Therefore, this test plan contain 3 parts:
* UDP dst port dynamically config for eCPRI
* rss supporting for eCPRI
* fdir supporting for eCPRI


Prerequisites
=============
1. Hardware:
    columbiaville_25g/columbiaville_100g

2. Software:
    dpdk: http://dpdk.org/git/dpdk
    scapy: http://www.secdev.org/projects/scapy/

3. Copy ice_wireless pkg to /lib/firmware/updates/intel/ice/ddp/ice.pkg

4. load driver::

    rmmod ice
    insmod ice.ko

5. Generate 4 VFs on PF0 and set mac address(not all the VFs are used)::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    ./usertools/dpdk-devbind.py -s
    0000:18:01.0 'Ethernet Adaptive Virtual Function 1889' if=enp24s1 drv=iavf unused=vfio-pci
    0000:18:01.1 'Ethernet Adaptive Virtual Function 1889' if=enp24s1f1 drv=iavf unused=vfio-pci
    0000:18:01.2 'Ethernet Adaptive Virtual Function 1889' if=enp24s1f2 drv=iavf unused=vfio-pci
    0000:18:01.3 'Ethernet Adaptive Virtual Function 1889' if=enp24s1f3 drv=iavf unused=vfio-pci

    ip link set ens785f0 vf 0 mac 00:11:22:33:44:55
    ip link set ens785f0 vf 1 mac 00:11:22:33:44:11
    ip link set ens785f0 vf 2 mac 00:11:22:33:44:22
    ip link set ens785f0 vf 3 mac 00:11:22:33:44:33

6. Set VF0 as trust::

    ip link set ens785f0 vf 0 trust on

7. Bind 3 VFs to dpdk driver, keep one VF in kernel::

    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0 0000:18:01.1 0000:18:01.2

8. Launch dpdk on VF0, VF1 and VF2, and VF0 request DCF mode::

    ./dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf -a 0000:18:01.1 -a 0000:18:01.2 -- -i

    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start
    testpmd> show port info all

    check the VF0 driver is net_ice_dcf.

9. For test case 01 and test case 02, need to add print log in testpmd to show the eCPRI ptype, then compile DPDK again:

diff --git a/drivers/net/iavf/iavf_rxtx.c b/drivers/net/iavf/iavf_rxtx.c
 index af5a28d84..3dbd5ab97 100644
 --- a/drivers/net/iavf/iavf_rxtx.c
 +++ b/drivers/net/iavf/iavf_rxtx.c
 @@ -1314,6 +1314,8 @@ iavf_recv_pkts_flex_rxd(void *rx_queue,
                 rxm->ol_flags = 0;
                 rxm->packet_type = ptype_tbl[IAVF_RX_FLEX_DESC_PTYPE_M &
                         rte_le_to_cpu_16(rxd.wb.ptype_flex_flags0)];
 +                printf("++++++++++++ptype=%u\n",
 +                       IAVF_RX_FLEX_DESC_PTYPE_M & rte_le_to_cpu_16(rxd.wb.ptype_flex_flags0));
                 iavf_flex_rxd_to_vlan_tci(rxm, &rxd);
                 rxq->rxd_to_pkt_fields(rxq, rxm, &rxd);
                 pkt_flags = iavf_flex_rxd_error_to_pkt_flags(rx_stat_err0);
 @@ -2346,7 +2348,7 @@ iavf_set_rx_function(struct rte_eth_dev *dev)
                 IAVF_DEV_PRIVATE_TO_ADAPTER(dev->data->dev_private);
         struct iavf_info *vf = IAVF_DEV_PRIVATE_TO_VF(dev->data->dev_private);

 -#ifdef RTE_ARCH_X86
 +#if 0
         struct iavf_rx_queue *rxq;
         int i;
         bool use_avx2 = false;
 @@ -2446,6 +2448,7 @@ iavf_set_rx_function(struct rte_eth_dev *dev)
                 else
                         dev->rx_pkt_burst = iavf_recv_pkts;
         }
 +        dev->rx_pkt_burst = iavf_recv_pkts_flex_rxd;
  }

  /* choose tx function*/
 --


Test case 01: add and delete eCPRI port config in DCF
=====================================================
1. add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

2. send eCPRI pkts to VF1, check the pattern can be parsed correctly:

MAC_IPV4_UDP_ECPRI_MSGTYPE0(ptype=372)::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC0(ptype=373)::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x00')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC1(ptype=374)::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x01')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC3(ptype=375)::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x03')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC5(ptype=376)::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x05')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC6(ptype=377)::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x06')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC7(ptype=378)::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x07')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2(ptype=379)::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x08')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE5(ptype=380)::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x05')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI(ptype=381)::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x06')], iface="ens786f0")

3. send eCPRI pkts which udp dport is not matched the config to VF1, check the pattern can not be recognized(all the ptype is 24)::

MAC_IPV4_UDP_ECPRI_MSGTYPE0::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5121)/Raw('\x10\x00')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC0::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5121)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x00')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC1::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5121)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x01')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC3::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5121)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x03')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC5::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5121)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x05')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC6::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5121)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x06')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC7::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5121)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x07')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5121)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x08')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE5::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5121)/Raw('\x10\x05')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5121)/Raw('\x10\x06')], iface="ens786f0")

4. send same eCPRI pkts in step 2 to VF2, check the pattern can be parsed correctly.

5. delete eCPRI port config in DCF::

    port config 0 udp_tunnel_port rm ecpri 0x5123

6. send same eCPRI pkts in step 2 to VF1, check the pattern can not be recognized(all the ptype is 24).


Test case 02: test eCPRI port config when DCF exit and reset
============================================================
1. add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

2. quit testpmd, then Launch testpmd again::

    ./dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf -a 0000:18:01.1 0000:18:01.2 -- -i
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

3. send eCPRI pkts which udp dport is match before config to VF1, check the pattern can not be recognized(all the ptype is 24)::

MAC_IPV4_UDP_ECPRI_MSGTYPE0::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC0::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x00')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC1::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x01')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC3::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x03')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC5::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x05')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC6::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x06')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2_SEC7::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x07')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE2::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x02')/Raw('x'*11)/Raw('\x08')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI_MSGTYPE5::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x05')], iface="ens786f0")

MAC_IPV4_UDP_ECPRI::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x06')], iface="ens786f0")

4. add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

5. reset DCF by set mac address::

    ip link set ens785f0 vf 0 mac 00:11:22:33:44:66

6. send eCPRI pkts in step 3 to VF1, check the pattern can not be recognized(all the ptype is 24).

7. quit testpmd, then Launch testpmd again, add eCPRI port config in DCF::

    ./dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf -a 0000:18:01.1 0000:18:01.2 -- -i
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start
    testpmd> port config 0 udp_tunnel_port add ecpri 0x5123

8. reset DCF by set trust off::

    ip link set ens785f0 vf 0 trust off

9. send eCPRI pkts in step 3 to VF1, check the pattern can not be recognized(all the ptype is 24).


Test case 03: test DCF port config and linux port config
========================================================
1. add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

2. add linux port config, check the cmd can not config successfully::

    ip link add vx0 type vxlan id 100 local 1.1.1.1 remote 2.2.2.2 dev ens785f0 dstport 0x1234
    ifconfig vx0 up
    ifconfig vx0 down

    [1825286.116930] ice 0000:18:00.0: Cannot config tunnel, the capability is used by DCF

3. delete eCPRI port config in DCF::

    port config 0 udp_tunnel_port rm ecpri 0x5123

4. add linux port config, check the cmd can config successfully::

    ifconfig vx0 up
    ifconfig vx0 down

5. quit testpmd, then Launch testpmd again::

    ./dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf -a 0000:18:01.1 -a 0000:18:01.2 -- -i
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

6. add linux port config::

    ip link add vx0 type vxlan id 100 local 1.1.1.1 remote 2.2.2.2 dev ens785f0 dstport 0x1234
    ifconfig vx0 up

7. add eCPRI port config in DCF::

    testpmd> port config 0 udp_tunnel_port add ecpri 0x5123
    ice_dcf_send_aq_cmd(): No response (201 times) or return failure (desc: -63 / buff: -63)
    udp tunneling port add error: (No such process)

   check the cmd can not config successfully.

8. remove linux port config::

    ifconfig vx0 down

9. add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

   check the cmd can config successfully.


Test case 04: negative eCPRI port config in DCF
===============================================
1. try below negative cmd in testpmd::

    testpmd> port config 1 udp_tunnel_port add ecpri 0x5123
    udp tunneling port add error: (Operation not supported)

    testpmd> port config 5 udp_tunnel_port add ecpri 0x5123
    Invalid port 5

    testpmd> port config 15 udp_tunnel_port rm ecpri 0x5123
    Invalid port 15

    testpmd> port config a udp_tunnel_port add ecpri 0x5123
    Bad arguments

    testpmd> port config 0 udp_tunnel_port add ecpri 0
    udp tunneling port add error: (Permission denied)

    testpmd> port config 0 udp_tunnel_port rm ecpri 0
    udp tunneling port add error: (Operation not permitted)

    testpmd> port config 0 udp_tunnel_port add ecpri ffff
    Bad arguments

    testpmd> port config 0 udp_tunnel_port add ecpri 0xffff
    udp tunneling port add error: (Permission denied)


Test case 05: rss for udp ecpri
===============================

1. Add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

2. Validate rule::

    flow validate 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end

3. Create rule and list rule::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end

4. Send a basic hit pattern packet, record the hash value,
   check the packet is distributed to queues by RSS::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")

5. Send hit pattern packets with changed input set in the rule,
   check the received packets have different hash values with basic packet,
   check the packets are distributed to queues by rss::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x47')], iface="ens786f0")

6. Destroy the rule and list rule::

    testpmd> flow destroy 1 rule 0
    testpmd> flow list 1

7. Send same packets with step 4 and 5,
   check received packets don't have hash value or hash value is same, rule can't work.


Test case 06: rss for eth_ecpri
===============================

1. Start testpmd without DCF mode::

    dpdk-testpmd -c f -n 4 -a 18:01.1 -- -i --rxq=16 --txq=16

2. Validate rule::

    flow validate 1 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end

3. Create rule and list rule::

    flow create 1 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end

4. Send a basic hit pattern packet, record the hash value,
   check the packet is distributed to queues by RSS::

    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")

5. Send hit pattern packets with changed input set in the rule,
   check the received packets have different hash values with basic packet,
   check the packets are distributed to queues by rss::

   sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")
   sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x47')], iface="ens786f0")

6. Destroy the rule and list rule::

    testpmd> flow destroy 1 rule 0
    testpmd> flow list 1

7. Send same packet with step 4,
   check received packets don't have hash value or hash value is same, rule can't work.


Test case 07: rss multirules + multiports
=========================================

1. Add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

2. Create multi rules::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end
    flow create 1 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end
    flow create 2 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end
    flow create 2 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end

3. Send a basic hit pattern packet, record the hash value,
   check the packets are distributed to queues by RSS::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:22")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:22", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")

4. Send hit pattern packets with changed input set in the rule,
   check the received packets have different hash value with basic packet,
   check the packets are distributed to queues by rss::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:22")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:22", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")

5. Destroy the rule and list rule::

    testpmd> flow destroy 1 rule 0
    testpmd> flow list 1
    testpmd> flow destroy 2 rule 0
    testpmd> flow list 2

6. Send same packet with step 3,
   check received packets don't have hash value or hash value is same, rule can't work.


Test case 08: rss without/with udp port set for udp ecpri rule
==============================================================

1. Create rule and list rule without udp port config::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end

2. Send basic hit pattern packets, record the hash value,
   check parser is wrong, hash value is same,
   RSS eCPRI UDP rule will return success, but not work::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x47')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x48')], iface="ens786f0")

3. Add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

4. Send basic hit pattern packets, check hash values are different.
   check the packets are distributed to queues by RSS::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")


Test case 09: DCF reset for udp ecpri rss
=========================================

1. Add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

2. Create rule::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end

3. Send a basic hit pattern packet, record the hash value,
   check the packet is distributed to queues by RSS::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")

4. Send hit pattern packet with changed input set in the rule,
   check the received packet has different hash value with basic packet,
   check the packet is distributed to queues by rss::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")

5. Reset DCF by set mac address::

    ip link set ens785f0 vf 0 mac 00:11:22:33:44:11

6. Send packets, check packets parser are wrong, check don't have or hash value is same::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x47')], iface="ens786f0")

7. Reset DCF by set mac address::

    ip link set ens785f0 vf 0 mac 00:11:22:33:44:55

8. Quit testpmd and repeat step 1~6, get same result.

8. Reset DCF by set trust off::

    ip link set ens785f0 vf 0 trust off

9. Repeat step 6, result is same.

10. Set VF0 as trust::

    ip link set ens785f0 vf 0 trust on


Test case 10: DCF reset for eth ecpri rss
=========================================

1. Create rule::

    flow create 1 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end

2. Send a basic hit pattern packet, record the hash value,
   check the packet is distributed to queues by RSS::

    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")

3. Send hit pattern packet with changed input set in the rule,
   check the received packet has different hash value with basic packet,
   check the packet is distributed to queues by rss::

    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")

4. Reset DCF by set mac address::

    ip link set ens785f0 vf 0 mac 00:11:22:33:44:11

5. Send packets, check the received packets have different hash values, rule can work::

    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x47')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x48')], iface="ens786f0")

6. Reset DCF by set trust off::

    ip link set ens785f0 vf 0 trust off

7. Repeat step 1~5, result is same.

8. Set VF0 as trust::

    ip link set ens785f0 vf 0 trust on

9. Reset DCF by set mac address::

    ip link set ens785f0 vf 0 mac 00:11:22:33:44:55


Test case 11: DCF exit for eth ecpri and udp ecpri rss
======================================================

1. Start testpmd with dcf mode on vf0::

    ./dpdk-testpmd -c 0xff -n 6 -a 0000:18:01.0,cap=dcf --file-prefix=test1 -- -i
    port config 0 udp_tunnel_port add ecpri 0x5123

2. Start testpmd with iavf mode on vf1 and vf2::

    ./dpdk-testpmd -c 0xff -n 6 -a 0000:60:01.1 -a 0000:60:01.2 --file-prefix=test2 -- -i --rxq=16 --txq=16
    flow create 0 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end
    flow create 1 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end

3. Send a basic hit pattern packet, record the hash value,
   check the packets are distributed to queues by RSS::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:22", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")

4. Send hit pattern packets with changed input set in the rule,
   check the received packets have different hash values with basic packet,
   check the packets are distributed to queues by rss::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:22", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")

5. Quit dcf testpmd.

6. Repeat 3 and 4 steps, check udp ecpri parser is wrong and rule can't work.
   Check eth ecpri rule can work, has different hash values.


Test case 12: eCPRI over Ethernet header pattern fdir
=====================================================
matched packets::

    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")

unmatched packets::

    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")

Enable RSS of eCPRI over Ethernet header in advance::

    flow create 1 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end

Subcase 1: queue index
----------------------

1. validate fdir rule, and no rule listed::

    flow validate 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions queue index 3 / mark id 1 / end

2. create filter rules::

    flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions queue index 3 / mark id 1 / end

3. send matched packets, check the packets are distributed to queue 3 with FDIR matched ID=0x1.
   send unmatched packets, check the packets are distributed by RSS without FDIR matched ID.

4. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 1 rule 1

5. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no fdir rule listed.

subcase 2: rss queues
---------------------
1. validate fdir rule, and no rule listed::

    flow validate 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions rss queues 5 6 end / mark id 2 / end

2. create fdir rule::

    flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions rss queues 5 6 end / mark id 2 / end

3. send matched packets, check the packets are distributed to queue 5 or 6 with FDIR matched ID=0x2.
   send unmatched packets, check the packets are distributed by RSS without FDIR matched ID.

4. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 1 rule 1

5. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no fdir rule listed.

subcase 3: drop
---------------
1. validate fdir rule, and no rule listed::

    flow validate 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions drop / end

2. create fdir rule::

    flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions drop / end

3. send matched packets, check the packets are dropped.
   send unmatched packets, check the packets are distributed by RSS without FDIR matched ID.

4. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 1 rule 1

5. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no fdir rule listed.

subcase 4: passthru
-------------------
1. validate fdir rule, and no rule listed::

    flow validate 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions passthru / mark id 1 / end

2. create fdir rule::

    flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions passthru / mark id 1 / end

3. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x1.
   send unmatched packets, check the packets are distributed by RSS without FDIR matched ID.

4. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 1 rule 1

5. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no fdir rule listed.

subcase 5: mark + rss
---------------------
1. validate fdir rule, and no rule listed::

    flow validate 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions mark / rss / end

2. create fdir rule::

    flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions mark / rss / end

3. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send unmatched packets, check the packets are distributed by RSS without FDIR matched ID.

4. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 1 rule 1

5. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no fdir rule listed.

subcase 6: mark
---------------
1. validate fdir rule, and no rule listed::

    flow validate 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions mark / end

2. create fdir rule::

    flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions mark / end

3. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send unmatched packets, check the packets are distributed by RSS without FDIR matched ID.

4. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 1 rule 1

5. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no fdir rule listed.


Test case 13: eCPRI over IP/UDP header pattern fdir
===================================================
matched packets::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")

unmatched packets::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")

Add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

Enable RSS of eCPRI over IP/UDP header in advance::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end

Subcase 1: queue index
----------------------

1. validate fdir rule, and no rule listed::

    flow validate 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions queue index 2 / mark / end

2. create filter rules::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions queue index 2 / mark / end

3. send matched packets, check the packets are distributed to queue 2 with FDIR matched ID=0x0.
   send unmatched packets, check the packets are distributed by RSS without FDIR matched ID.

4. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 1 rule 1

5. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no fdir rule listed.

subcase 2: rss queues
---------------------
1. validate fdir rule, and no rule listed::

    flow validate 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions rss queues 5 6 end / mark id 2 / end

2. create fdir rule::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions rss queues 5 6 end / mark id 2 / end

3. send matched packets, check the packets are distributed to queue 5 or 6 with FDIR matched ID=0x2.
   send unmatched packets, check the packets are distributed by RSS without FDIR matched ID.

4. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 1 rule 1

5. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no fdir rule listed.

subcase 3: drop
---------------
1. validate fdir rule, and no rule listed::

    flow validate 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions drop / end

2. create fdir rule::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions drop / end

3. send matched packets, check the packets are dropped.
   send unmatched packets, check the packets are distributed by RSS without FDIR matched ID.

4. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 1 rule 1

5. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no fdir rule listed.

subcase 4: passthru
-------------------
1. validate fdir rule, and no rule listed::

    flow validate 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions passthru / mark id 1 / end

2. create fdir rule::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions passthru / mark id 1 / end

3. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x1.
   send unmatched packets, check the packets are distributed by RSS without FDIR matched ID.

4. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 1 rule 1

5. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no fdir rule listed.

subcase 5: mark + rss
---------------------
1. validate fdir rule, and no rule listed::

    flow validate 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions mark / rss / end

2. create fdir rule::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions mark / rss / end

3. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send unmatched packets, check the packets are distributed by RSS without FDIR matched ID.

4. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 1 rule 1

5. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no fdir rule listed.

subcase 6: mark
---------------
1. validate fdir rule, and no rule listed::

    flow validate 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions mark / end

2. create fdir rule::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions mark / end

3. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send unmatched packets, check the packets are distributed by RSS without FDIR matched ID.

4. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 1 rule 1

5. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no fdir rule listed.


Test case 14: ecpri fdir multirules
===================================
Add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

Enable RSS for eCPRI over MAC/UDP::

    flow create 1 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end
    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end
    flow create 2 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end
    flow create 2 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end

1. create multi rules::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions rss queues 5 6 end / mark id 0 / end
    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2346 / end actions passthru / mark id 1 / end
    flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions drop / end
    flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2346 / end actions queue index 1 / mark id 2 / end
    flow create 2 ingress pattern eth / ecpri common type iq_data pc_id is 0x2346 / end actions mark id 3 / end
    flow create 2 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2346 / end actions mark / rss / end

2. send matched packets and unmatched packets::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:22", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:22", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:22")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:22")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x46')], iface="ens786f0")

3. check results:
   pkt1 to queue 5 or 6 with mark id 0
   pkt2 is distributed by rss with mark id 1
   pkt3 drop
   pkt4 to queue 1 with mark id 2
   pkt5 is distributed by rss
   pkt6 is distributed by rss with mark id 3
   pkt7 is distributed by rss
   pkt8 is distributed by rss with mark id 0


Test case 15: ecpri fdir negative case
======================================
1. create ecpri over IP/UDP fdir rule without setting DCF eCPRI port::

    testpmd> flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions rss queues 5 6 end / mark id 0 / end
    iavf_fdir_add(): Failed to add rule request due to no hw resource
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

2. check there is no rule listed.


Test case 16: ecpri fdir when DCF reset
=======================================
1. add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

   create two fdir rules::

    flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions queue index 1 / mark id 1 / end
    flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions queue index 2 / mark id 2 / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")

   check pkt1 is to queue 1 with mark id 1, pkt2 is to queue 2 with mark id 2

3. reset DCF by set mac address::

    ip link set enp59s0f0 vf 0 mac 00:11:22:33:44:11

4. send same packets, check pkt1 is distributed by rss without mark id, pkt2 is to queue 2 with mark id 2

5. quit testpmd and repeat step 1 and step 2, get same results.

6. reset DCF by set trust off::

    ip link set enp59s0f0 vf 0 trust off

7. send same packets check pkt1 is distributed by rss without mark id, pkt2 is to queue 2 with mark id 2.


Test case 17: ecpri fdir when DCF exit
======================================
1. start testpmd with dcf mode on vf0::

    ./dpdk-testpmd -c 0xff -n 6 -a 0000:18:01.0,cap=dcf --file-prefix=vf0 -- -i

   add eCPRI port config in DCF::

    port config 0 udp_tunnel_port add ecpri 0x5123

2. start testpmd with iavf mode on vf1 and vf2::

    ./dpdk-testpmd -c 0xff00 -n 6 -a 0000:18:01.1 -a 0000:18:01.2 --file-prefix=vf1 -- -i --rxq=16 --txq=16

   create two fdir rules::

    flow create 0 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions queue index 1 / mark id 1 / end
    flow create 0 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions queue index 2 / mark id 2 / end

3. send packets::

    sendp([Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=0x5123)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:11", type=0xAEFE)/Raw('\x10\x00\x02\x24\x23\x45')], iface="ens786f0")

   check pkt1 is to queue 1 with mark id 1, pkt2 is to queue 2 with mark id 2

4. quit dcf testpmd, send same packets,
   check pkt1 is distributed by rss without mark id, pkt2 is to queue 2 with mark id 2.
