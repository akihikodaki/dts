.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2018 Intel Corporation

==============================================
PMD drivers adaption for new RXTX offload APIs
==============================================
Description
===========

   Adapt all the Intel drivers for the new RX/TX offload APIs.
   There're new RX/TX offload APIs accepted in 17.11,
   These new APIs are more friendly and easier to use.
   Currently, they co-exist with the old APIs. Some adaption work is
   here to make the drivers can use the old ones or the new ones.
   But suppose the target is to let all the NICs support the new APIs
   and then remove the old ones.
   So, in driver layer, we can begin to support the new ones and remove
   the old ones.
   Eight new commands are added.

   Rx test commands::

    testpmd > show port <port_id> rx_offload capabilities
    testpmd > show port <port_id> rx_offload configuration
    testmpd > port config <port_id> rx_offload <offload> on|off
    testpmd > port <port_id> rxq <queue_id> rx_offload <offload> on|off

   Tx test commands::

    testpmd > show port <port_id> tx_offload capabilities
    testpmd > show port <port_id> tx_offload configuration
    testmpd > port config <port_id> tx_offload <offload> on|off
    testpmd > port <port_id> txq <queue_id> tx_offload <offload> on|off

Prerequisites
=============

1. Hardware:
   Intel® Ethernet 700 Series and 82599/500 Series

2. Software:
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Bind the pf port to dpdk driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0 05:00.1

4. There are different capabilities between i40e and ixgbe.
   So define different test cases for the two types of NIC.
   There is no rx_offload per_queue parameter in i40e setting now.
   There is no tx_offload per_queue parameter in ixgbe setting now.

   i40e::

    testpmd> show port 0 rx_offload capabilities
    Rx Offloading Capabilities of port 0 :
      Per Queue :
      Per Port  : VLAN_STRIP IPV4_CKSUM UDP_CKSUM TCP_CKSUM QINQ_STRIP OUTER_IPV4_CKSUM VLAN_FILTER VLAN_EXTEND JUMBO_FRAME SCATTER KEEP_CRC

    testpmd> show port 0 tx_offload capabilities
    Tx Offloading Capabilities of port 0 :
      Per Queue : MBUF_FAST_FREE
      Per Port  : VLAN_INSERT IPV4_CKSUM UDP_CKSUM TCP_CKSUM SCTP_CKSUM TCP_TSO OUTER_IPV4_CKSUM QINQ_INSERT VXLAN_TNL_TSO GRE_TNL_TSO IPIP_TNL_TSO GENEVE_TNL_TSO MULTI_SEGS

   ixgbe::

    testpmd> show port 0 rx_offload capabilities
    Rx Offloading Capabilities of port 0 :
      Per Queue : VLAN_STRIP
      Per Port  : IPV4_CKSUM UDP_CKSUM TCP_CKSUM TCP_LRO MACSEC_STRIP VLAN_FILTER VLAN_EXTEND JUMBO_FRAME SCATTER SECURITY KEEP_CRC

    testpmd> show port 0 tx_offload capabilities
    Tx Offloading Capabilities of port 0 :
      Per Queue :
      Per Port  : VLAN_INSERT IPV4_CKSUM UDP_CKSUM TCP_CKSUM SCTP_CKSUM TCP_TSO MACSEC_INSERT MULTI_SEGS SECURITY


Rx Offload
==========

Test case: Rx offload per-port setting in command-line
======================================================

1. Enable rx cksum in command-line::

    ./<build_target>/app/dpdk-testpmd -c f -n 4 -- -i --rxq=4 --txq=4 --enable-rx-cksum
    testpmd> set fwd csum
    testpmd> set verbose 1
    testpmd> show port 0 rx_offload configuration
    Rx Offloading Configuration of port 0 :
      Port : IPV4_CKSUM UDP_CKSUM TCP_CKSUM
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :

1) Send packets::

    pkt1=Ether(dst="00:00:00:00:01:00", src="52:00:00:00:00:00")/IP(src="10.0.0.1")/TCP()/("X"*46)
    pkt2=Ether(dst="00:00:00:00:01:00", src="52:00:00:00:00:00")/IP(chksum=0x0)/TCP(chksum=0xf)/("X"*46)
    pkt3=Ether(dst="00:00:00:00:01:00", src="52:00:00:00:00:00")/IP(src="10.0.0.1")/UDP(chksum=0xf)/("X"*46)
    pkt4=Ether(dst="00:00:00:00:01:00", src="52:00:00:00:00:00")/IP(chksum=0x0)/UDP()/("X"*46)

2) Check the rx flags::

    RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD
    RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_BAD
    RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD
    RTE_MBUF_F_RX_L4_CKSUM_UNKNOWN RTE_MBUF_F_RX_IP_CKSUM_BAD

2. Disable the rx cksum per_port::

    testpmd> port stop 0
    testpmd> port config 0 rx_offload udp_cksum off
    testpmd> show port 0 rx_offload configuration
    Rx Offloading Configuration of port 0 :
      Port : IPV4_CKSUM TCP_CKSUM
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :
    testpmd> port start 0

   The port can start normally.
   Try this step with "tcp_cksum/ipv4_cksum", the port can start normally.

3. Enable the rx cksum per_port, all the configuration can be set successfully.
   The port can start normally.

Test case: Rx offload per-port and per_queue setting
=====================================================

1. Check all the rx_offload capability::

    testpmd> show port 0 rx_offload capabilities

2. Enable and disable per_port and per_queue capabilities.

   Check the configuration and the port can start normally.

Test case: 82599/500 Series Rx offload per-queue setting
========================================================

1. Start testpmd::

    ./<build_target>/app/dpdk-testpmd -c f -n 4 -- -i --rxq=4 --txq=4
    testpmd> set fwd mac
    testpmd> set verbose 1
    testpmd> show port info all
    VLAN offload:
    strip off

2. Show the rx_offload configuration::

    testpmd> show port 0 rx_offload configuration
    Rx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :

3. Enable vlan_strip per_queue::

    testpmd> port stop 0
    testpmd> port 0 rxq 0 rx_offload vlan_strip on
    testpmd> port 0 rxq 2 rx_offload vlan_strip on
    testpmd> port start 0
    testpmd> show port 0 rx_offload configuration
    Rx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] : VLAN_STRIP
      Queue[ 1] :
      Queue[ 2] : VLAN_STRIP
      Queue[ 3] :
    testpmd> show port info 0
    VLAN offload:
    strip on

4. Send two packets::

    pkt1 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(vlan=1)/IP(src="192.168.0.1", dst="192.168.0.3")/UDP(sport=33,dport=34)/Raw('x'*20)
    pkt2 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(vlan=1)/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=33,dport=34)/Raw('x'*20)

   Port0 receive the two packets in queue2 and queue3.
   Queue2 should capture strip vlan information like "VLAN tci=0x1" and "RTE_MBUF_F_RX_VLAN_STRIPPED",
   queue3 doesn't support vlan strip.

   If set "set fwd mac",
   Check the tester port connected to port1 which receive the forwarded packet
   So you can check that there is vlan id in pkt1, while there is not vlan id in pkt2.
   The result is consistent to the DUT port receive packets.

5. Disable vlan_strip per_queue::

    testpmd> port stop 0
    testpmd> port 0 rxq 3 rx_offload vlan_strip on
    testpmd> port 0 rxq 2 rx_offload vlan_strip off
    testpmd> port start 0
    testpmd> show port 0 rx_offload configuration
    Rx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] : VLAN_STRIP
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] : VLAN_STRIP

   Send the same packets,
   Queue3 should capture strip vlan information like "VLAN tci=0x1" and "RTE_MBUF_F_RX_VLAN_STRIPPED",
   queue2 doesn't support vlan strip.

6. Enable vlan_strip per_port::

    testpmd> port stop 0
    testpmd> port config 0 rx_offload vlan_strip on
    testpmd> port start 0
    testpmd> show port 0 rx_offload configuration
    Rx Offloading Configuration of port 0 :
      Port : VLAN_STRIP
      Queue[ 0] : VLAN_STRIP
      Queue[ 1] : VLAN_STRIP
      Queue[ 2] : VLAN_STRIP
      Queue[ 3] : VLAN_STRIP

  Send the two packets. queue3 and queue2 both implement vlan_strip

7. Disable vlan_strip per_port::

    testpmd> port stop 0
    testpmd> port config 0 rx_offload vlan_strip off
    testpmd> port start 0
    testpmd> show port 0 rx_offload configuration
    Rx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :

    testpmd> show port info 0
    VLAN offload:
    strip off

   send the two packets. queue3 and queue2 both don't support vlan_strip

   Note 1: there is no rx_offload per_queue parameter in i40e driver,
   so this case is just only for ixgbe.

   Note 2: per_port setting has higher priority than per_queue setting.
   If you has set an offload by port, you can't change the setting by queue.

Tx Offload
==========

Test case: Tx offload per-port setting
======================================

1. Start testpmd::

    ./<build_target>/app/dpdk-testpmd -c 0x6 -n 4  -- -i --rxq=4 --txq=4 --port-topology=loop
    testpmd> set fwd txonly
    testpmd> set verbose 1
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :
    testpmd> start

   Tester port0 received the packet.
   There is no vlan infomation in the received packet.

2. Enable vlan_insert per_port::

    testpmd> port stop 0
    testpmd> port config 0 tx_offload vlan_insert on
    testpmd> tx_vlan set 0 1
    testpmd> port start 0
    Configuring Port 0 (socket 0)
    Port 0: 90:E2:BA:AC:9B:44
    Checking link statuses...
    Done
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port : VLAN_INSERT
      Queue[ 0] : VLAN_INSERT
      Queue[ 1] : VLAN_INSERT
      Queue[ 2] : VLAN_INSERT
      Queue[ 3] : VLAN_INSERT
    testpmd> start

   Tester port0 receive the packet.
   There is vlan ID in the received packet.

3. Disable vlan_insert per_port::

    testpmd> port stop 0
    testpmd> port config 0 tx_offload vlan_insert off
    testpmd> port start 0
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :
    testpmd> start

   There is no vlan infomation in the received packet.
   The disable command takes effect.

Test case: Tx offload per-port setting in command-line
======================================================

1. Start testpmd with "--tx-offloads"::

    ./<build_target>/app/dpdk-testpmd -c 0xf -n 4  -- -i --rxq=4 --txq=4 --port-topology=loop --tx-offloads=0x0001
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port : VLAN_INSERT
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :

   Set the insert vlan ID::

    testpmd> port stop 0
    testpmd> tx_vlan set 0 1
    testpmd> port start 0
    testpmd> set fwd txonly
    testpmd> start

   Tester port0 can receive the packets with vlan ID.

2. Disable vlan_insert per_queue::

    testpmd> port stop 0
    testpmd> port 0 txq 0 tx_offload vlan_insert off
    testpmd> port 0 txq 1 tx_offload vlan_insert off
    testpmd> port 0 txq 2 tx_offload vlan_insert off
    testpmd> port 0 txq 3 tx_offload vlan_insert off
    testpmd> port start 0
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port : VLAN_INSERT
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :
    testpmd> start

   The tester port0 still receive packets with vlan ID.
   The per_port capability can't be disabled by per_queue command.

3. Disable vlan_insert per_port::

    testpmd> port stop 0
    testpmd> port config 0 tx_offload vlan_insert off
    testpmd> port start 0
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :
    testpmd> start

   The tester port receive packets without vlan ID.
   The per_port capability can be disabled by per_port command.

4. Enable vlan_insert per_queue::

    testpmd> port stop 0
    testpmd> port 0 txq 0 tx_offload vlan_insert on
    testpmd> port 0 txq 1 tx_offload vlan_insert on
    testpmd> port 0 txq 2 tx_offload vlan_insert on
    testpmd> port 0 txq 3 tx_offload vlan_insert on
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] : VLAN_INSERT
      Queue[ 1] : VLAN_INSERT
      Queue[ 2] : VLAN_INSERT
      Queue[ 3] : VLAN_INSERT
    testpmd> port start 0
    Configuring Port 0 (socket 0)
    Ethdev port_id=0 tx_queue_id=0, new added offloads 0x1 must be within pre-queue offload capabilities 0x0 in rte_eth_tx_queue_setup()
    Fail to configure port 0 tx queues

   The port failed to start.
   The per_port capability can't be enabled by per_queue command.

5. Enable vlan_insert per_port::

    testpmd> port stop 0
    testpmd> port config 0 tx_offload vlan_insert on
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port : VLAN_INSERT
      Queue[ 0] : VLAN_INSERT
      Queue[ 1] : VLAN_INSERT
      Queue[ 2] : VLAN_INSERT
      Queue[ 3] : VLAN_INSERT
    testpmd> port start 0
    testpmd> start

   The tester port received packets with vlan ID.
   The per_port capability can be enabled by per_port command.

Test case: Tx offload checksum
==============================

1. Set checksum forward mode::

    ./<build_target>/app/dpdk-testpmd -c f -n 4 -- -i --rxq=4 --txq=4
    testpmd> set fwd csum
    testpmd> set verbose 1
    testpmd> show port 0 tx_offload configuration
    Rx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :

1) Send an ipv4-udp packet to the port::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src="100.0.0.1", dst="100.0.0.2")/UDP(sport=1024,dport=1025)], iface="enp131s0f3")

2) Check the tx flags::

    RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

2. Enable the tx ipv4_cksum of port 1::

    testpmd> port stop 1
    testpmd> port config 1 tx_offload ipv4_cksum on
    testpmd> show port 1 tx_offload configuration
    Tx Offloading Configuration of port 1 :
      Port : IPV4_CKSUM
      Queue[ 0] : IPV4_CKSUM
      Queue[ 1] : IPV4_CKSUM
      Queue[ 2] : IPV4_CKSUM
      Queue[ 3] : IPV4_CKSUM
    testpmd> port start 1
    testpmd> start

   The port can start normally.

3. Send an ipv4-udp packet to the port::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src="100.0.0.1", dst="100.0.0.2")/UDP(sport=1024,dport=1025)], iface="enp131s0f3")

   There is printing "RTE_MBUF_F_TX_IP_CKSUM" and "RTE_MBUF_F_TX_L4_NO_CKSUM" in the tx line.

4. Disable tx ipv4_cksum and enable tx udp_cksum,
   then send the same ipv4-udp packet, there is printing "RTE_MBUF_F_TX_UDP_CKSUM",
   but no "RTE_MBUF_F_TX_IP_CKSUM".

5. Try step 4 with "tcp_cksum" on, then send an ipv4-tcp packet::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src="100.0.0.1", dst="100.0.0.2")/TCP(sport=1024,dport=1025)], iface="enp131s0f3")

   There is printing "RTE_MBUF_F_TX_TCP_CKSUM".

6. Try step 4 with "sctp_cksum" on, then send an ipv4-sctp packet::

    sendp([Ether(dst="00:00:00:00:01:00")/IP(src="100.0.0.1", dst="100.0.0.2")/sctp(sport=1024,dport=1025)], iface="enp131s0f3")

   There is printing "RTE_MBUF_F_TX_SCTP_CKSUM".

Test case: Tx offload per-queue and per-port setting
====================================================

1. Check all the tx_offload capability::

    testpmd> show port 0 tx_offload capabilities

2. Enable and disable per_port and per_queue capabilities.

   Check the configuration and the port can start normally.

Test case: Intel® Ethernet 700 Series Tx offload per-queue setting
==================================================================

1. Start testpmd and get the tx_offload capability and configuration::

    ./<build_target>/app/dpdk-testpmd -c f -n 4 -- -i --rxq=4 --txq=4
    testpmd> show port 0 tx_offload capabilities
    Tx Offloading Capabilities of port 0 :
      Per Queue : MBUF_FAST_FREE
      Per Port  : VLAN_INSERT IPV4_CKSUM UDP_CKSUM TCP_CKSUM SCTP_CKSUM TCP_TSO OUTER_IPV4_CKSUM QINQ_INSERT VXLAN_TNL_TSO GRE_TNL_TSO IPIP_TNL_TSO GENEVE_TNL_TSO MULTI_SEGS
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port : MBUF_FAST_FREE
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :

2. Disable mbuf_fast_free per_port::

    testpmd> port stop 0
    testpmd> port config 0 tx_offload mbuf_fast_free off
    testpmd> port start 0
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :

3. Enable mbuf_fast_free per_queue::

    testpmd> port stop 0
    testpmd> port 0 txq 0 tx_offload mbuf_fast_free on
    testpmd> port 0 txq 1 tx_offload mbuf_fast_free on
    testpmd> port 0 txq 2 tx_offload mbuf_fast_free on
    testpmd> port 0 txq 3 tx_offload mbuf_fast_free on
    testpmd> port start 0
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] : MBUF_FAST_FREE
      Queue[ 1] : MBUF_FAST_FREE
      Queue[ 2] : MBUF_FAST_FREE
      Queue[ 3] : MBUF_FAST_FREE
    testpmd> start

   The port fwd can be started normally.

4. Disable mbuf_fast_free per_queue::

    testpmd> port stop 0
    testpmd> port 0 txq 0 tx_offload mbuf_fast_free off
    testpmd> port 0 txq 1 tx_offload mbuf_fast_free off
    testpmd> port 0 txq 2 tx_offload mbuf_fast_free off
    testpmd> port 0 txq 3 tx_offload mbuf_fast_free off
    testpmd> port start 0
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :

5. Enable mbuf_fast_free per_port::

    testpmd> port stop 0
    testpmd> port config 0 tx_offload mbuf_fast_free on
    testpmd> port start 0
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port : MBUF_FAST_FREE
      Queue[ 0] : MBUF_FAST_FREE
      Queue[ 1] : MBUF_FAST_FREE
      Queue[ 2] : MBUF_FAST_FREE
      Queue[ 3] : MBUF_FAST_FREE
    testpmd> start

   The port fwd can be started normally.

   Note 1: there is no tx_offload per_queue parameter in ixgbe driver,
   so this case is just only for i40e.

Test case: Tx offload multi_segs setting
======================================================

1. Start testpmd with "--tx-offloads=0x00008000" to enable tx_offload multi_segs ::

    ./<build_target>/app/dpdk-testpmd -c 0xf -n 4  -- -i --tx-offloads==0x00008000
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port : MULTI_SEGS
      Queue[ 0] : MULTI_SEGS

2. Set fwd to txonly, Set the length of each segment of the TX-ONLY packets, Set the split policy for TX packets, then start to send pkgs::

    testpmd> set fwd txonly
    testpmd> set txpkts 64,128,512,2000,64,128,512,2000
    testpmd> set txsplit rand
    testpmd> start

3. Check TX-packets will not hang and continue to increase::
    Wait 30s or more, check TX-packets will continue to increase and can be more than 100K

    testpmd> show port stats all
        ######################## NIC statistics for port 0  ########################
        RX-packets: 0         RX-missed: 0          RX-bytes:  0
        RX-errors: 0
        RX-nombuf:  0
        TX-packets: 102628493  TX-errors: 0          TX-bytes:  139709164375

        Throughput (since last show)
        Rx-pps:            0          Rx-bps:            0
        Tx-pps:       563539          Tx-bps:   9892394768
        ############################################################################

        ######################## NIC statistics for port 1  ########################
        RX-packets: 0         RX-missed: 0          RX-bytes:  0
        RX-errors: 0
        RX-nombuf:  0
        TX-packets: 102627429  TX-errors: 0          TX-bytes:  139709724215

        Throughput (since last show)
        Rx-pps:            0          Rx-bps:            0
        Tx-pps:       563708          Tx-bps:   9892375000
        ############################################################################

    testpmd> stop
    testpmd> quit

4. Start testpmd again without "--tx-offloads", check multi-segs is disabled by default::

    ./<build_target>/app/dpdk-testpmd -c 0xf -n 4  -- -i
    testpmd> show port 0 tx_offload configuration
    No MULTI_SEGS in Tx Offloading Configuration of ports

5. Enable tx_offload multi_segs ::

    testpmd> port stop all
    testpmd> port config 0 tx_offload multi_segs on
    testpmd> port config 1 tx_offload multi_segs on
    testpmd> port start all
    testpmd> show port 0 tx_offload configuration
    Tx Offloading Configuration of port 0 :
      Port : MULTI_SEGS
      Queue[ 0] : MULTI_SEGS

6. Set fwd to txonly, Set the length of each segment of the TX-ONLY packets, Set the split policy for TX packets, then start to send pkgs::

    testpmd> set fwd txonly
    testpmd> set txpkts 64,128,256,512,64,128,256,512
    testpmd> set txsplit rand
    testpmd> start

7. Check TX-packets will not hang and continue to increase::
    Wait 30s or more, check TX-packets will continue to increase and can be more than 100K

    testpmd> show port stats all
        ######################## NIC statistics for port 0  ########################
        RX-packets: 0         RX-missed: 0          RX-bytes:  0
        RX-errors: 0
        RX-nombuf:  0
        TX-packets: 101266875  TX-errors: 0          TX-bytes:  136721429135

        Throughput (since last show)
        Rx-pps:            0          Rx-bps:            0
        Tx-pps:       563293          Tx-bps:   9892438256
        ############################################################################

        ######################## NIC statistics for port 1  ########################
        RX-packets: 0         RX-missed: 0          RX-bytes:  0
        RX-errors: 0
        RX-nombuf:  0
        TX-packets: 101265405  TX-errors: 0          TX-bytes:  136721996771

        Throughput (since last show)
        Rx-pps:            0          Rx-bps:            0
        Tx-pps:       564392          Tx-bps:   9892193416
        ############################################################################

    testpmd> stop
    testpmd> quit
