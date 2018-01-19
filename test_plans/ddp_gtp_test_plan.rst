.. Copyright (c) <2017>, Intel Corporation
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

===============================
Fortville DDP GTP-C/GTP-U Tests
===============================

FVL6 supports DDP (Dynamic Device Personalization) to program analyzer/parser
via AdminQ. Profile can be used to update FVL configuration tables via MMIO
configuration space, not microcode or firmware itself. For microcode/FW
changes new HW/FW/NVM image must be uploaded to the NIC. Profiles will be
stored in binary files and need to be passed to AQ to program FVL during
initialization stage.

GPRS Tunneling Protocol (GTP) is a group of IP-based communications 
protocols used to carry general packet radio service (GPRS) within GSM, 
UMTS and LTE networks. GTP can be decomposed into separate protocols, 
GTP-C, GTP-U. 
With DDP, new types GTP-C/GTP-U tunnels can be supported. To make it 
scalable it is preferable to use DDP API to get information about new 
PCTYPE/PTYPEs defined a profile, instead of hardcoding i40e PCTYPE/PTYPE 
mapping to DPDK FlowType/PacketType.

Below features have be enabled for GTP-C/GTP-U:

1. FDIR for GTP-C/GTP-U to direct different TEIDs to different queues

2. Tunnel filters for GTP-C/GTP-U to direct different TEIDs to different VFs


Prerequisites
=============

1. Host PF in DPDK driver::

    ./tools/dpdk-devbind.py -b igb_uio 81:00.0

2. Create 1 VF from 1 PF with DPDK driver::

    echo 1 > /sys/bus/pci/devices/0000:81:00.0/max_vfs

3. Detach VF from the host::

    rmmod i40evf

4. Pass through VF 81:10.0 to vm0, start vm0.

5. Login vm0, then bind VF0 device to igb_uio driver.

6. Start testpmd on host and vm0, host supports flow director and cloud
   filter, VM supports cloud filter. If test PF flow director, need to add 
   --pkt-filter-mode=perfect on testpmd to enable flow director, set chained 
   port topology mode, add txq/rxq to enable multi-queues. In general, PF's 
   max queue is 64, VF's max queue is 4::

    ./testpmd -c f -n 4 -- -i --pkt-filter-mode=perfect --port-topology=chained --tx-offloads=0x8fff --txq=64 --rxq=64  


Test Case: Load dynamic device personalization 
================================================

1. Stop testpmd port before loading profile::

    testpmd > port stop all

2. Load profile gtp.pkgo which is a binary file::

    testpmd > ddp add (port_id) (profile_path)

3. Check profile information successfully::

    testpmd > ddp get list (port_id)

4. Start testpmd port::

    testpmd > port start all

Note:

1. Gtp.pkgo profile is not released by ND yet, only have engineer version for
   internal use so far. Plan to keep public reference profiles at Intel 
   Developer Zone, release versions of profiles and supply link later.

2. Loading DDP is the prerequisite for below GTP relative cases. Load 
   profile again once restarting testpmd to let software detect this 
   event, although has “profile has already existed” reminder. Operate
   global reset or lanconf tool to recover original setting. Global reset
   trigger reg is 0xb8190, first cmd is core reset, second cmd is global
   reset::

    testpmd > write reg 0 0xb8190 1
    testpmd > write reg 0 0xb8190 2
	  

Test Case: GTP-C FDIR packet for PF
===================================

1. Add GTP-C flow director rule for PF, set TEID as random 20 bits, port is 
   2123, queue should be among configured queue number::
   
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / gtpc teid is 0x3456 / end actions queue index 12 / end

2. Set fwd rxonly, enable output and start PF and VF testpmd.

3. Send GTP-C packet with good checksum, dport is 2123, TEID is same
   as configured rule::
   
    p=Ether()/IP()/UDP(dport=2123)/GTP_U_Header(teid=0x3456)/Raw('x'*20) 

4. Check PF could receive configured TEID GTP-C packet, checksum is good,
   queue is configured queue, ptypes are correct, check PKT_RX_FDIR print.

5. Send GTP-C packet with bad checksum, dport is 2123, TEID is same
   as configured rule::
   
    p=Ether()/IP()/UDP(chksum=0x1234,dport=2123)/GTP_U_Header(teid=0x3456)/Raw('x'*20) 
   
6. Check PF could receive configured TEID GTP packet, checksum is good, 
   queue is configured queue, ptypes are correct, check PKT_RX_FDIR print.
   
7. Send some TEIDs are not same as configured rule or other types packets, 
   check checksum are good, queue is 0, ptypes are correct, check no 
   PKT_RX_FDIR print.
  

Test Case: GTP-C Cloud filter packet for PF
===========================================

1. Add GTP-C cloud filter rule for PF, set TEID as random 20 bits, port is 
   2123, queue should be among configured queue number::
   
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / gtpc teid is 0x12345678 / end actions pf / queue index 3 / end

2. Set fwd rxonly, enable output and start PF and VF testpmd.

3. Send GTP-C packet with good checksum, dport is 2123, TEID is same
   as configured rule::
   
    p=Ether()/IP()/UDP(dport=2123)/GTP_U_Header(teid=0x12345678)/Raw('x'*20)

4. Check PF could receive configured TEID GTP-C packet, checksum is good,
   queue is configured queue, ptypes are correct, check no PKT_RX_FDIR print.

5. Send GTP-C packet with bad checksum, dport is 2123, TEID is same
   as configured rule::
   
    p=Ether()/IP()/UDP(chksum=0x1234,dport=2123)/GTP_U_Header(teid=0x12345678)/Raw('x'*20)

6. Check PF could receive configured TEID GTP packet, checksum is good, 
   queue is configured queue, ptypes are correct, check no PKT_RX_FDIR print.

7. Send some TEIDs are not same as configured rule or other types packets, 
   check checksum are good, queue is 0, ptypes are correct, no 
   PKT_RX_FDIR print.


Test Case: GTP-U FDIR packet for PF
===================================

1. Add GTP-U flow director rule for PF, set TEID as random 20 bits, port is 
   2152, queue should be among configured queue number::
   
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x123456 / end actions queue index 18 / end
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x123456 / ipv4 / end actions queue index 58 / end
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x123456 / ipv6 / end actions queue index 33 / end

2. Set fwd rxonly, enable output and start PF and VF testpmd.

3. Send GTP-U packet with good checksum, dport is 2152, TEID is same
   as configured rule::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x123456)/Raw('x'*20)
    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x123456)/IP()/Raw('x'*20)
    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x123456)/IPv6()/Raw('x'*20)

4. Check PF could receive configured TEID GTP-U packet, checksum is good,
   queue is configured queue, ptypes are correct, check PKT_RX_FDIR print.
   
5. Send GTP-U packet with bad checksum, dport is 2152, TEID is same
   as configured rule::

    p=Ether()/IP()/UDP(chksum=0x1234,dport=2152)/GTP_U_Header(teid=0x123456)/Raw('x'*20)
    p=Ether()/IP()/UDP(chksum=0x1234,dport=2152)/GTP_U_Header(teid=0x123456)/IP()/Raw('x'*20)
    p=Ether()/IP()/UDP(chksum=0x1234,dport=2152)/GTP_U_Header(teid=0x123456)/IPv6()/Raw('x'*20)

6. Check PF could receive configured TEID GTP packet, checksum is good, queue 
   is configured queue, ptypes are corrcet, check PKT_RX_FDIR print.
   
7. Send some TEIDs are not same as configured rule or other types packets, 
   check checksum are good, queue is 0, pytpes are correct, check no 
   PKT_RX_FDIR print.


Test Case: GTP-U Cloud filter packet for PF
===========================================

1. Add GTP-U cloud filter rule for PF, set TEID as random 20 bits, port is 
   2152, queue should be among configured queue number::
   
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions pf / queue index 3 / end

2. Set fwd rxonly, enable output and start PF and VF testpmd.

3. Send GTP-U packet with good checksum, dport is 2152, TEID is same
   as configured rule::
   
    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12345678)/Raw('x'*20)
   		
4. Check PF could receive configured TEID GTP-U packet, checksum is good,
   queue is configured queue, ptypes are correct, check no PKT_RX_FDIR print.

5. Send GTP-U packet with bad checksum, dport is 2152, TEID is same
   as configured rule::
   
    p=Ether()/IP()/UDP(chksum=0x1234,dport=2152)/GTP_U_Header(teid=0x12345678)/Raw('x'*20)

6. Check PF could receive configured TEID GTP packet, checksum is good, queue
   is configured queue, ptypes are correct, check no PKT_RX_FDIR print.

7. Send some TEIDs are not same as configured rule or other types packets, 
   check checksum are good, queue is 0, ptypes are correct, no 
   PKT_RX_FDIR print.
   
   
Test Case: GTP-C Cloud filter packet for VF
===========================================

1. Add GTP-C cloud filter rule for VF, set TEID as random 20 bits, port is 
   2123, queue should be among configured queue number::
   
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / gtpc teid is 0x1678 / end actions vf id 0 / queue index 3 / end

2. Set fwd rxonly, enable output and start PF and VF testpmd.
	
3. Send GTP-C packet with good checksum, dport is 2123, TEID is same
   as configured rule::
   
    p=Ether()/IPv6()/UDP(dport=2123)/GTP_U_Header(teid=0x1678)/Raw('x'*20) 

4. Check VF could receive configured teid GTP-C packet, checksum is good,
   queue is configured queue.

5. Send GTP-C packet with bad checksum, dport is 2123, TEID is same
   as configured rule::
    
    p=Ether()/IPv6()/UDP(chksum=0x1234,dport=2123)/GTP_U_Header(teid=0x1678)/Raw('x'*20) 
   
6. Check VF could receive configured TEID GTP packet, checksum is good, queue 
   is configured queue.
   
   
Test Case: GTP-U Cloud filter packet for VF
===========================================

1. Add GTP-U cloud filter rule for VF, set TEID as random 20 bits, port is 2152, 
   queue should be among configured queue number::
   
    testpmd > flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x178 / end actions vf id 0 / queue index 1 / end

2. Set fwd rxonly, enable output and start PF and VF testpmd.

3. Send GTP-U packet with good checksum, dport is 2152, TEID is same
   as configured rule::
   
    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x178)/Raw('x'*20) 

4. Check VF could receive configured TEID GTP-U packet, checksum is good,
   queue is configured queue.

5. Send GTP-U packet with bad checksum, GTP-U dport is 2152, TEID is same
   as configured rule::
   
    p=Ether()/IPv6()/UDP(chksum=0x1234,dport=2152)/GTP_U_Header(teid=0x178)/Raw('x'*20) 
   
6. Check VF could receive configured TEID GTP packet, checksum is good, queue 
   is configured queue.
   

GTP packet
==========

Note:
   
1. List all of profile supported GTP packets as below, also could use "ddp get 
   info gtp.pkgo" to check profile information. Below left number is ptype 
   value, right are layer types.
   167: IPV4, GTP-C, PAY4

2. Scapy 2.3.3+ versions support to send GTP packet. Please check your scapy 
   tool could send below different GTP types' packets successfully then run 
   above tests.  
 

GTP-C packet types
==================

167: IPV4, GTP-C, PAY4::
    
    p=Ether()/IP()/UDP(dport=2123)/GTP_U_Header()/Raw('x'*20) 

168: IPV6, GTP-C, PAY4::
    
    p=Ether()/IPv6()/UDP(dport=2123)/GTP_U_Header()/Raw('x'*20)
 
GTP-U data packet types, IPv4 transport, IPv4 payload
=====================================================

169: IPV4 GTPU IPV4 PAY3::
      
    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/Raw('x'*20)

170: IPV4 GTPU IPV4FRAG PAY3::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(frag=5)/Raw('x'*20)

171: IPV4 GTPU IPV4 UDP PAY4::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/UDP()/Raw('x'*20)

172: IPV4 GTPU IPV4 TCP PAY4::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/TCP()/Raw('x'*20)

173: IPV4 GTPU IPV4 SCTP PAY4::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/SCTP()/Raw('x'*20)

174: IPV4 GTPU IPV4 ICMP PAY4::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/ICMP()/Raw('x'*20)

GTP-U data packet types, IPv6 transport, IPv4 payload
=====================================================

175: IPV6 GTPU IPV4 PAY3::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP()/Raw('x'*20)

176: IPV6 GTPU IPV4FRAG PAY3::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP(frag=5)/Raw('x'*20)

177: IPV6 GTPU IPV4 UDP PAY4::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP()/UDP()/Raw('x'*20)

178: IPV6 GTPU IPV4 TCP PAY4::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP()/TCP()/Raw('x'*20)

179: IPV6 GTPU IPV4 SCTP PAY4::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP()/SCTP()/Raw('x'*20)

180: IPV6 GTPU IPV4 ICMP PAY4::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP()/ICMP()/Raw('x'*20)

GTP-U control packet types 
==========================

181: IPV4, GTP-U, PAY4::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/Raw('x'*20)

182: PV6, GTP-U, PAY4::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/Raw('x'*20)
 
GTP-U data packet types, IPv4 transport, IPv6 payload
=====================================================

183: IPV4 GTPU IPV6FRAG PAY3::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)

184: IPV4 GTPU IPV6 PAY3::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/Raw('x'*20)

185: IPV4 GTPU IPV6 UDP PAY4::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/UDP()/Raw('x'*20)

186: IPV4 GTPU IPV6 TCP PAY4::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/TCP()/Raw('x'*20)

187: IPV4 GTPU IPV6 SCTP PAY4::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/SCTP()/Raw('x'*20)

188: IPV4 GTPU IPV6 ICMPV6 PAY4::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(nh=58)/ICMP()/Raw('x'*20) 

GTP-U data packet types, IPv6 transport, IPv6 payload
=====================================================

189: IPV6 GTPU IPV6 PAY3::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IPv6()/Raw('x'*20)

190: IPV6 GTPU IPV6FRAG PAY3::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)

191: IPV6 GTPU IPV6 UDP PAY4::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IPv6()/UDP()/Raw('x'*20)

113: IPV6 GTPU IPV6 TCP PAY4::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IPv6()/TCP()/Raw('x'*20)

120: IPV6 GTPU IPV6 SCTP PAY4::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IPv6()/SCTP()/Raw('x'*20)

128: IPV6 GTPU IPV6 ICMPV6 PAY4::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IPv6(nh=58)/ICMP()/Raw('x'*20)   
   
