.. Copyright (c) <2018>, Intel Corporation
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
   FVL/NNT

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

Test case: Rx offload per-port setting
======================================

1. Enable jumboframe when start testpmd::

    ./testpmd -c f -n 4 -- -i --rxq=4 --txq=4 --max-pkt-len=9000
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start
    testpmd> show port 0 rx_offload configuration
    Rx Offloading Configuration of port 0 :
      Port : JUMBO_FRAME
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :

2. Improve the tester ports's mtu::

    ifconfig enp131s0f0 mtu 9200
    ifconfig enp131s0f1 mtu 9200

   Send a jumboframe packet::

    pkt1 = Ether(dst="52:54:00:00:00:01", src="52:00:00:00:00:00")/IP(dst="192.168.0.1", src="192.168.0.2", len=8981)/Raw(load="P"*8961)
    pkt2 = Ether(dst="52:54:00:00:00:01", src="52:00:00:00:00:00")/IP(dst="192.168.0.1", src="192.168.0.3", len=8981)/Raw(load="P"*8961)

   pkt1 was distributed to queue 1, pkt2 was distributed to queue 0.

3. Failed to disable jumboframe per_queue::

    testpmd> port stop 0
    testpmd> port 0 rxq 1 rx_offload jumbo_frame off
    testpmd> port start 0

   The port can be started normally, but the setting doesn't take effect.
   Pkt1 still can be distributed to queue 1.

4. Succeed to disable jumboframe per_port::

    testpmd> port stop 0
    testpmd> port config 0 rx_offload jumbo_frame off
    testpmd> port start 0
    testpmd> show port 0 rx_offload configuration
    Rx Offloading Configuration of port 0 :
      Port :
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :
    testpmd> start

   Send the same two packet, there is no packet received.

5. Failed to enable jumboframe per_queue::

    testpmd> port stop 0
    testpmd> port 0 rxq 1 rx_offload jumbo_frame on
    testpmd> port start 0
    Configuring Port 0 (socket 0)
    Ethdev port_id=0 rx_queue_id=1, new added offloads 0x800 must be within pre-queue offload capabilities 0x1 in rte_eth_rx_queue_setup()
    Fail to configure port 0 rx queues

6. Succeed to enable jumboframe per_port::

    testpmd> port stop 0
    testpmd> port config 0 rx_offload jumbo_frame on
    testpmd> port start 0
    testpmd> show port 0 rx_offload configuration
    Rx Offloading Configuration of port 0 :
      Port : JUMBO_FRAME
      Queue[ 0] : JUMBO_FRAME
      Queue[ 1] : JUMBO_FRAME
      Queue[ 2] : JUMBO_FRAME
      Queue[ 3] : JUMBO_FRAME

   Send the same two packet, pkt1 was distributed to queue 1,
   pkt2 was distributed to queue 0.

Test case: Rx offload per-port setting in command-line
======================================================

1. Enable rx cksum in command-line::

    ./testpmd -c f -n 4 -- -i --rxq=4 --txq=4 --enable-rx-cksum
    testpmd> show port 0 rx_offload configuration
    Rx Offloading Configuration of port 0 :
      Port : IPV4_CKSUM UDP_CKSUM TCP_CKSUM
      Queue[ 0] :
      Queue[ 1] :
      Queue[ 2] :
      Queue[ 3] :

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

Test case: NNT Rx offload per-queue setting
===========================================

1. Start testpmd::

    ./testpmd -c f -n 4 -- -i --rxq=4 --txq=4
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
   Queue2 should capture strip vlan information like "VLAN tci=0x1" and "PKT_RX_VLAN_STRIPPED",
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
   Queue3 should capture strip vlan information like "VLAN tci=0x1" and "PKT_RX_VLAN_STRIPPED",
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

    ./testpmd -c 0x6 -n 4  -- -i --rxq=4 --txq=4 --port-topology=loop
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

    ./testpmd -c 0xf -n 4  -- -i --rxq=4 --txq=4 --port-topology=loop --tx-offloads=0x0001
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

Test case: Tx offload per-queue and per-port setting
====================================================

1. Check all the tx_offload capability::

    testpmd> show port 0 tx_offload capabilities

2. Enable and disable per_port and per_queue capabilities.

   Check the configuration and the port can start normally.

Test case: FVL Tx offload per-queue setting
===========================================

1. Start testpmd and get the tx_offload capability and configuration::

    ./testpmd -c f -n 4 -- -i --rxq=4 --txq=4
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
