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

==========
DDP L2TPV3
==========

DDP profile 0x80000004 adds support for directing L2TPv3 packets based on
their session ID for FVL NIC. For DDP introduction, please refer to :

 https://software.intel.com/en-us/articles/dynamic-device-personalization-for-intel-ethernet-700-series

l2tpv3oip-l4.pkg defines and supports below pctype packets, also
could check the information using command “ddp get info <profile>”
after loading the profile. left numbers are pctype values,right are
supported packets::

    28: IPV4 L2TPV3
    38: IPV6 L2TPV3

Packet Classifier types and Its Input Set

  +--------------+--------+-----------------------+-------------------------+
  | Packet Type  | PCType |    Hash Input Set     |      FD Input Set       |
  +--------------+--------+-----------------------+-------------------------+
  | IPv4,L2TPv3  |  28    |   L2TPv3 Session ID   |    L2TPv3 Session ID    |
  +--------------+--------+-----------------------+-------------------------+
  | IPv6,L2TPv3  |  38    |   L2TPv3 Session ID   |    L2TPv3 Session ID    |
  +--------------+--------+-----------------------+-------------------------+


Requirements as below
=====================

Flow API support for flow director rules based on L2TPv3 session ID
The current scope is limited to FVL NIC

Prerequisites
=============

1. DPDK version 20.02 or greater

2. I40E NIC with FW version 6.0 or greater

   In your linux terminal enter ethtool -i <interface-name> , this prints out
   the driver details.
   Ex  ::

    root@hostname:~/dpdk# ethtool -i <interface-name>
    driver: i40e
    version: 2.1.14-k
    firmware-version: 7.10 0x80006474 1.2527.0
    expansion-rom-version:
    bus-info: 0000:02:00.1
    supports-statistics: yes
    supports-test: yes
    supports-eeprom-access: yes
    supports-register-dump: yes
    supports-priv-flags: yes

*Note: If the firmware version is below 6.0 , the NIC does not support
any DDP functionality*

3. Download and extract L2TPv3 package

   https://downloadcenter.intel.com/download/28941/Dynamic-Device-Personalization-L2TPv3

4. Bind the Port to the userspace Driver <igb_uio/vfio-pci)::

    ./usertools/dpdk-devbind.py -b <igb_uio/vfio-pci> <PCI address of device to bind>

5. Start the TESTPMD::

    ./<build>/app/dpdk-testpmd -c f -n 4 -a
    <PCI address of device> -- -i --port-topology=chained --txq=64 --rxq=64
    --pkt-filter-mode=perfect

   For testpmd commands refer: https://doc.dpdk.org/guides/testpmd_app_ug/

6. Set Verbose

   To enable verbose logging in the testpmd application to get detailed
   information about rx queues and packet metadata::

    testpmd > set verbose 1

7. To enable required fields as per the indices in the L2TPv3 Packet field
   vector (refer Dynamic_Device_Personalization_L2TPv3_Rev1.x)

   To enable the specific field in the vector for a PCTYPE , the following
   command may be used::

    testpmd> port config <port_id> pctype <PCTYPE> fdir_inset set field
    <field_index>

   To check if a specific field in the vector is set for a PCTYPE, the
   following command may be used::

    testpmd> port config <port_id> pctype <PCTYPE> fdir_inset get field
    <field_index>

   To clear any specific field in the vector for a PCTYPE, the following
   command may be used::

    testpmd> port config <port_id> pctype  <pctype> fdir_inset clear field
    <field_index>

   To clear all fields for a specific PCTYPE, the following commands may
   be used::

    testpmd> port config <port_id> pctype <PCTYPE> fdir_inset clear all

*NOTE: Changes such as enabling/disabling of specific field in the vector
for a PCTYPE will remain applied across restarts of testpmd application.
It is good practice to explicitly set the desired field in the vector for
a PCTYPE upon start of testpmd.*


Test Case : Adding L2TPv3 profile to the port
=============================================

1. Stop testpmd port before loading profile::

    testpmd > port stop <port_id>

2. Load l2tpv3oip-l4.pkg file to the memory buffer and save the existing
   configuration to the l2tpv3oip-l4.bak file::

    testpmd > ddp add <port_id> <path>/l2tpv3oip-l4.pkg,<path>/
    l2tpv3oip-l4.bak

3. Check to see if the profile is loaded ::

    testpmd> ddp get list <port_id>
    Track id:     0x80000004
    Version:      1.0.0.0
    Profile name: L2TPv3oIP with L4 payload

Test Case : Deleting L2TPv3 profile from the port
=================================================

This test is intended to revert to the original DDP profile of the port
without reset

1. Stop testpmd port before loading profile::

    testpmd > port stop <port_id>

2. Remove profile from the network adapter and restore original
   configuration::

    testpmd > ddp del <port_id> <path>/l2tpv3oip-l4.bak

3. Check to see if the profile is deleted::

    testpmd> ddp get list <port_id>
    Profile number is: 0

Test Case : Adding and deleting Flow Director rules
===================================================

1. To Add l2tpv3 flow director rules::

    testpmd> flow create <port_id> ingress pattern eth / ipv4 / l2tpv3oip session_id
    is 1 / end actions queue index 1 / end
    testpmd> flow create <port_id> ingress pattern eth / ipv4 / l2tpv3oip session_id
    is 2 / end actions queue index 2 / end
    testpmd> flow create <port_id> ingress pattern eth / ipv4 / l2tpv3oip session_id
    is 3 / end actions queue index 3 / end

2. To List the rules using the flow list command with port number::

    testpmd> flow list <port_id>
       ID      Group   Prio    Attr    Rule
       0       0       0       i--     ETH IPV4 L2TPV3 => QUEUE
       1       0       0       i--     ETH IPV4 L2TPV3 => QUEUE
       2       0       0       i--     ETH IPV4 L2TPV3 => QUEUE

3. To delete a single rule ::

    testpmd> flow destroy <port_id> rule 0
    Flow rule #0 destroyed
    testpmd> flow list <port_id>
       ID      Group   Prio    Attr    Rule
       1       0       0       i--     ETH IPV4 L2TPV3 => QUEUE
       2       0       0       i--     ETH IPV4 L2TPV3 => QUEUE
      <flow rule with ID 0 should not be listed>

4. To delete all the rules::

    testpmd> flow flush <port_id>
    testpmd> flow list <port_id>
    testpmd>
    (No List is printed)

Test Case: L2TPv3 over IPv4 packet
==================================

1. Add l2tpv3 flow director rule, set sessionID as 1, queue 1::

    testpmd> flow create <port_id> ingress pattern eth / ipv4 / l2tpv3oip session_id
    is 1 / end actions queue index 1 / end

2. Send L2TPv3 packet with session ID matching the configured rule, Packets
   should be received on queue 1::

    p=Ether()/IP(proto=115)/Raw('\x00\x00\x00\x01')/Raw('x' * 20)

3. Send L2TPv3 packet with session ID not matching the configured rule,
   Packet should be received on queue 0::

    p=Ether()/IP(proto=115)/Raw('\x00\x00\x00\x11')/Raw('x' * 20)

Test Case: L2TPv3 over IPv6 packet
==================================

1. Add l2tpv3 flow director rule, set sessionID as 1000, queue 2::

    testpmd> flow create <port_id> ingress pattern eth / ipv6 / l2tpv3oip session_id
    is 1000 / end actions queue index 2 / end

2. Send L2TPv3 packet with session ID matching the configured rule, Packets
   should be received on queue 2::

    p=Ether()/IPv6(nh=115)/Raw('\x00\x00\x03\xe8')/Raw('x' * 20)

3. Send L2TPv3 packet with session ID not matching the configured rule,
   Packet should be received on queue 0::

    p=Ether()/IPv6(nh=115)/Raw('\x00\x00\x03\x88')/Raw('x' * 20)

Test Case: L2TPv3oIPv4 with L2TPv3oIPv6 configuration
========================================================

1. Add l2tpv3 flow director rules  , set sessionID as 1001, queue 1 for IPv4
   and IPv6 flows::

    testpmd> flow create <port_id> ingress pattern eth / ipv4 / l2tpv3oip session_id
    is 1001 / end actions queue index 1 / end

    testpmd> flow create <port_id> ingress pattern eth / ipv6 / l2tpv3oip session_id
    is 1001 / end actions queue index 1 / end

2. Send L2TPv3 packets for IPv4 and IPv6 with session ID same as configured
   rule, Packets should be received on queue 1::

    P_IPV4=Ether()/IP(proto=115)/Raw('\x00\x00\x03\xe9')/Raw('x' * 20)

    P_IPV6=Ether()/IPv6(nh=115)/Raw('\x00\x00\x03\xe9')/Raw('x' * 20)


3. Send L2TPv3 packets(IPv4 and IPv6) with session ID not matching the
   configured rules, Packet should be received on queue 0::

    P_IPV4=Ether()/IP(proto=115)/Raw('\x00\x00\x03\xf9')/Raw('x' * 20)

    P_IPV6=Ether()/IPv6(nh=115)/Raw('\x00\x00\x03\xf9')/Raw('x' * 20)

Test Case: UDP, L2TPv3oIPv4 with L2TPv3oIPv6 configurations
============================================================

1. Add l2tpv3 flow director rules , set sessionID as 1001, queue 1 for IPv4
   and queue 2 for IPv6 flows::

    testpmd> flow create <port_id> ingress pattern eth / ipv4 / l2tpv3oip session_id
    is 1001 / end actions queue index 1 / end

    testpmd> flow create <port_id> ingress pattern eth / ipv6 / l2tpv3oip session_id
    is 1001 / end actions queue index 2 / end

2. Add UDP flow director rule , set queue 3 for UDP packets::

    testpmd> flow create <port_id> ingress pattern eth / ipv4 / udp / end actions
    queue index 3 / end

3. Send L2TPv3 packets for IPv4 and IPv6 with session ID same as configured
   rules, Packets should be received on queue 1 and queue 2 respectively::

    P_IPV4=Ether()/IP(proto=115)/Raw('\x00\x00\x03\xe9')/Raw('x' * 20)

    P_IPV6=Ether()/IPv6(nh=115)/Raw('\x00\x00\x03\xe9')/Raw('x' * 20)

4. Send L2TPv3 packets(IPv4 and IPv6) with session ID not matching the
   configured rules, Packet should be received on queue 0::

    P_IPV4=Ether()/IP(proto=115)/Raw('\x00\x00\x03\x09')/Raw('x' * 20)

    P_IPV6=Ether()/IPv6(nh=115)/Raw('\x00\x00\x03\x09')/Raw('x' * 20)

5. Send IPv4/UDP packet. Verify that the packet is received on queue 3::

    P_UDP=Ether()/IP()/UDP()

Test Case: L2TPv3oIPv4 configuration with specific SIP and DIP
==============================================================

1. Stop testpmd port before loading profile::

    testpmd > port stop <port_id>

2. Set the fdir inset as follows::

    testpmd> port config <port_id> pctype <pctype> fdir_inset clear all
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 15
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 16
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 27
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 28
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 44
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 45

3. Start testpmd port ::

    testpmd> port start <port_id>

4. Start forwarding::

    testpmd> start

5. Add l2tpv3 flow director rule, set sessionID as 1 queue 1::

    testpmd> flow create <port_id> ingress pattern eth / ipv4 src is 10.10.10.1 dst
    is 20.10.10.20 / l2tpv3oip session_id is 1 / end actions queue index 10
    / end

6. Send L2TPv3 packet with SIP,DIP and session ID matching the configured rule,
   Packets should be received on queue 10::

    p=Ether()/IP(src="10.10.10.1",dst="20.10.10.20",proto=115)/
    Raw('\x00\x00\x00\x01')/Raw('x' * 20)

7. Send L2TPv3 packet with session ID not matching the configured rule,
   Packet should be received on queue 0::

    p=Ether(src="00:00:00:00:00:02", dst="3C:FD:FE:A5:49:88")/IP(proto=115)
    /Raw('\x00\x00\x00\x44')/Raw('x' * 20)

8. Send L2TPv3 packet with SIP not matching the configured rule,
   Packets should be received on queue 10::

    p=Ether()/IP(src="100.10.10.1",dst="20.10.10.20",proto=115)/
    Raw('\x00\x00\x00\x01')/Raw('x' * 20)

9. Send L2TPv3 packet with DIP not matching the configured rule,
   Packets should be received on queue 10::

    p=Ether()/IP(src="10.10.10.1",dst="200.10.10.20",proto=115)/
    Raw('\x00\x00\x00\x01')/Raw('x' * 20)

Test Case: L2TPv3oIPv6 configuration with specific SIP and DIP
==============================================================

1. Set the fdir inset as follows ::

    testpmd> port config <port_id> pctype <pctype> fdir_inset clear all
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 13
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 14
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 15
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 16
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 17
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 18
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 19
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 20
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 21
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 22
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 23
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 24
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 25
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 26
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 27
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 28
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 44
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 45

3. Start testpmd port ::

    testpmd> port start <port_id>

4. Start forwarding ::

    testpmd> start

5. Add l2tpv3 flow director rule, set sessionID as 1000 queue 20::

    testpmd> flow create <port_id> ingress pattern eth / ipv6 src is 1:2:3:4:5:6:7:8
    dst is 8:7:6:5:4:3:2:1 / l2tpv3oip session_id is 1000 / end actions queue
    index 20 / end

6. Send L2TPv3 packet with session ID, SIP and DIP matching the configured
   rule, Packets should be received on queue 20::

    p=Ether()/IPv6(src="1:2:3:4:5:6:7:8",dst="8:7:6:5:4:3:2:1",nh=115)/
    Raw('\x00\x00\x03\xe8')/Raw('x' * 20)

7. Send L2TPv3 packet with session ID not matching the configured rule,
   Packet should be received on queue 0::

    p=Ether()/IPv6(src="1:2:3:4:5:6:7:8",dst="8:7:6:5:4:3:2:1",nh=115)/
    Raw('\x00\x00\x03\xff')/Raw('x' * 20)

8. Send L2TPv3 packet with Source IP not matching the configured rule,
   Packet should be received on queue 0::

    p=Ether()/IPv6(src="1111:2:3:4:5:6:7:8",dst="8:7:6:5:4:3:2:1",nh=115)/
    Raw('\x00\x00\x03\xe8')/Raw('x' * 20)

9. Send L2TPv3 packet with Destination IP not matching the configured rule,
   Packet should be received on queue 0::

    p=Ether()/IPv6(src="1:2:3:4:5:6:7:8",dst="8:7:6:5:4:3:2:1111",nh=115)/
    Raw('\x00\x00\x03\xe8')/Raw('x' * 20)

Test Case: L2TPv3oIPv4 configuration with specific SIP
======================================================

1. Stop testpmd port before loading profile::

    testpmd > port stop all

2. Set the fdir inset as follows ::

    testpmd> port config <port_id> pctype <pctype> fdir_inset clear all
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 15
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 16
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 44
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 45

3. Start testpmd port ::

    testpmd> port start <port_id>

4. Start forwarding ::

    testpmd> start

5. Add l2tpv3 flow director rule, set sessionID as 1, queue 10::

    testpmd> flow create <port_id> ingress pattern eth / ipv4 src is 10.10.10.1 /
    l2tpv3oip session_id is 1 / end actions queue index 10 / end

6. Send L2TPv3 packet with SIP and session ID matching the configured rule,
   Packets should be received on queue 10::

    p=Ether()/IP(src="10.10.10.1",proto=115)/Raw('\x00\x00\x00\x01')/
    Raw('x' * 20)

7. Send L2TPv3 packet with session ID not matching the configured rule,
   Packet should be received on queue 0::


    p=Ether()/IP(src="10.10.10.1",proto=115)/Raw('\x00\x00\x00\x21')/
    Raw('x' * 20)

8. Send L2TPv3 packet with SIP not matching the configured rule, Packets
   should be received on queue 0::

    p=Ether()/IP(src="20.20.20.1",proto=115)/Raw('\x00\x00\x00\x01')/
    Raw('x' * 20)

Test Case: L2TPv3oIPv6 configuration with specific SIP
======================================================

1. Stop testpmd port before loading profile::

    testpmd > port stop <port_id>

2. Set the fdir inset as follows ::

    testpmd> port config <port_id> pctype <pctype> fdir_inset clear all
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 13
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 14
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 15
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 16
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 17
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 18
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 19
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 20
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 44
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 45

3. Start testpmd port ::

    testpmd> port start <port_id>

4. Start forwarding ::

    testpmd> start

5. Add l2tpv3 flow director rule, set sessionID as 1000, queue 20::

    testpmd> flow create <port_id> ingress pattern eth / ipv6 src is 1:2:3:4:5:6:7:8
    / l2tpv3oip session_id is 1000 / end actions queue index 20 / end

6. Send L2TPv3 packet with SIP and session ID matching the configured rule,
   Packets should be received on queue 20::

    p=Ether()/IPv6(src="1:2:3:4:5:6:7:8",nh=115)/Raw('\x00\x00\x03\xe8')/
    Raw('x' * 20)

7. Send L2TPv3 packet with session ID not matching the configured rule,
   Packet should be received on queue 0::

    p=Ether()/IPv6(src="1:2:3:4:5:6:7:8",nh=115)/Raw('\x00\x00\x03\xff')/
    Raw('x' * 20)

8. Send L2TPv3 packet with SIP not matching the configured rule, Packet
   should be received on queue 0::

    p=Ether()/IPv6(src="1111:2:3:4:5:6:7:8",nh=115)/Raw('\x00\x00\x03\xe8')/
    Raw('x' * 20)

Test Case: L2TPv3oIPv4 configuration with specific DIP
======================================================

1. Stop testpmd port before loading profile::

    testpmd > port stop <port_id>

2. Set the fdir inset as follows ::

    testpmd> port config <port_id> pctype <pctype> fdir_inset clear all
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 27
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 28
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 44
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 45

3. Start testpmd port ::

    testpmd> port start <port_id>

4. Start forwarding ::

    testpmd> start

5. Add l2tpv3 flow director rule, set sessionID as 1, queue 10::

    testpmd> flow create <port_id> ingress pattern eth / ipv4 dst is 20.10.10.20
    / l2tpv3oip session_id is 1 / end actions queue index 10 / end

6. Send L2TPv3 packet with DIP and session ID matching the configured rule,
   Packets should be received on queue 10::

    p=Ether()/IP(dst="20.10.10.20",proto=115)/Raw('\x00\x00\x00\x01')/
    Raw('x' * 20)

7. Send L2TPv3 packet with session ID not matching the configured rule,
   Packet should be received on queue 0::

    p=Ether()/IP(dst="20.10.10.20",proto=115)/Raw('\x00\x00\x00\x44')/
    Raw('x' * 20)

8. Send L2TPv3 packet with DIP not matching the configured rule, Packet
   should be received on queue 0::

    p=Ether()/IP(dst="2220.10.10.20",proto=115)/Raw('\x00\x00\x00\x01')/
    Raw('x' * 20)

Test Case: L2TPv3oIPv6 configuration with specific DIP
======================================================

1. Stop testpmd port before loading profile::

    testpmd > port stop <port_id>

2. Set the fdir inset as follows ::

    testpmd> port config <port_id> pctype <pctype> fdir_inset clear all
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 21
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 22
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 23
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 24
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 25
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 26
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 27
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 28
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 44
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 45

3. Start testpmd port ::

    testpmd> port start <port_id>

4. Start forwarding ::

    testpmd> start

5. Add l2tpv3 flow director rule, set sessionID as 1000, queue 20::

    testpmd> flow create <port_id> ingress pattern eth / ipv6 dst is 8:7:6:5:4:3:2:1
    / l2tpv3oip session_id is 1000 / end actions queue index 20 / end

6. Send L2TPv3 packet with session ID, DIP matching the configured rule,
   Packets should be received on queue 20::

    p=Ether()/IPv6(dst="8:7:6:5:4:3:2:1",nh=115)/Raw('\x00\x00\x03\xe8')/
    Raw('x' * 20)

7. Send L2TPv3 packet with session ID not matching the configured rule,
   Packet should be received on queue 0::

    p=Ether()/IPv6(dst="8:7:6:5:4:3:2:1",nh=115)/Raw('\x00\x00\x03\xff')/
    Raw('x' * 20)

8. Send L2TPv3 packet with DIP not matching the configured rule, Packet
   should be received on queue 0::

    p=Ether()/IPv6(dst="8888:7:6:5:4:3:2:1",nh=115)/Raw('\x00\x00\x03\xe8')/
    Raw('x' * 20)

Test Case: L2TPv3 with specific IPv4 SIP and IPv6 SIP configured together
=========================================================================

1. Stop testpmd port before loading profile::

    testpmd > port stop <port_id>

2. Set the fdir inset as follows ::

    testpmd> port config <port_id> pctype <pctype> fdir_inset clear all
    testpmd> port config <port_id> pctype <pctype> fdir_inset clear all
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 15
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 16
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 44
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 45
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 13
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 14
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 15
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 16
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 17
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 18
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 19
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 20
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 44
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 45

3. Start testpmd port ::

    testpmd> port start <port_id>

4. Start forwarding ::

    testpmd> start

5. Add l2tpv3 flow director rule,set sessionID as 1,queue 10 for IPv4 flow::

    testpmd> flow create <port_id> ingress pattern eth / ipv4 src is 10.10.10.1 /
    l2tpv3oip session_id is 1 / end actions queue index 10 / end

6. Add l2tpv3 flow director rule,set sessionID as 1000,
   queue 20 for IPv6 flow::

    testpmd> flow create <port_id> ingress pattern eth / ipv6 src is 1:2:3:4:5:6:7:8
    / l2tpv3oip session_id is 1000 / end actions queue index 20 / end

7. Send L2TPv3 IPv4 packet with SIP and session ID matching the configured
   rule, Packets should be received on queue 10::

    p=Ether()/IP(src="10.10.10.1",proto=115)/Raw('\x00\x00\x00\x01')/
    Raw('x' * 20)

8. Send L2TPv3 IPv4 packet with session ID not matching the configured rule,
   Packet should be received on queue 0::

    p=Ether()/IP(proto=115)/Raw('\x00\x00\x00\x44')/Raw('x' * 20)

9. Send L2TPv3 IPv4 packet with SIP not matching the configured rule,
   Packets should be received on queue 0::

    p=Ether()/IP(src="20.20.20.1",proto=115)/Raw('\x00\x00\x00\x01')/
    Raw('x' * 20)

10. Send L2TPv3 IPv6 packet with SIP and session ID matching the configured
    rule, Packets should be received on queue 20::

     p=Ether()/IPv6(src="1:2:3:4:5:6:7:8",nh=115)/Raw('\x00\x00\x03\xe8')/
     Raw('x' * 20)

11. Send L2TPv3 IPv6 packet with session ID not matching the configured
    rule, Packet should be received on queue 0::

     p=Ether()/IPv6(src="1:2:3:4:5:6:7:8",nh=115)/Raw('\x00\x00\x03\xff')
     /Raw('x' * 20)

12. Send L2TPv3 IPv6 packet with SIP not matching the configured rule,
    Packet should be received on queue 0::

     p=Ether()/IPv6(src="1111:2:3:4:5:6:7:8",nh=115)/Raw('\x00\x00\x03\xe8')
     /Raw('x' * 20)

Test Case: L2TPv3 with specific IPv4 DIP and IPv6 DIP configured together
=========================================================================

1. Stop testpmd port before loading profile::

    testpmd > port stop <port_id>

2. Set the fdir inset as follows ::

    testpmd> port config <port_id> pctype <pctype> fdir_inset clear all
    testpmd> port config <port_id> pctype <pctype> fdir_inset clear all
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 27
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 28
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 44
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 45
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 21
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 22
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 23
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 24
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 25
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 26
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 27
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 28
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 44
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 45

3. Start testpmd port ::

    testpmd> port start <port_id>

4. Start forwarding ::

    testpmd> start

5. Add l2tpv3 flow director rule, set sessionID as 1 queue 10 for IPv4::

    testpmd> flow create <port_id> ingress pattern eth / ipv4 dst is 20.10.10.20 /
    l2tpv3oip session_id is 1 / end actions queue index 10 / end

6. Add l2tpv3 flow director rule, set sessionID as 1000, queue 20 for IPv6::

    testpmd> flow create <port_id> ingress pattern eth / ipv6 dst is 8:7:6:5:4:3:2:1
    / l2tpv3oip session_id is 1000 / end actions queue index 20 / end

7. Send L2TPv3 IPv4 packet with DIP and session ID matching the configured
   rule,Packets should be received on queue 10::

    p=Ether()/IP(dst="20.10.10.20",proto=115)/Raw('\x00\x00\x00\x01')/
    Raw('x' * 20)

8. Send L2TPv3 IPv4 packet with session ID not matching the configured rule,
   Packet should be received on queue 0::

    p=Ether()/IP(dst="20.10.10.20",proto=115)/Raw('\x00\x00\x00\x21')/
    Raw('x' * 20)

9. Send L2TPv3 IPv4 packet with DIP not matching the configured rule, Packet
   should be received on queue 0::

    p=Ether()/IP(dst="2220.10.10.20",proto=115)/Raw('\x00\x00\x00\x01')/Raw('x' * 20)

10. Send L2TPv3 packet with session ID, DIP matching the configured rule,
    Packets should be received on queue 20::

     p=Ether()/IPv6(dst="8:7:6:5:4:3:2:1",nh=115)/Raw('\x00\x00\x03\xe8')/
     Raw('x' * 20)

11. Send L2TPv3 packet with session ID not matching the configured rule,
    Packet should be received on queue 0::

     p=Ether()/IPv6(dst="8:7:6:5:4:3:2:1",nh=115)/Raw('\x00\x00\x03\xff')/
     Raw('x' * 20)

12. Send L2TPv3 packet with DIP not matching the configured rule, Packet
    should be received on queue 0::

     p=Ether()/IPv6(dst="8888:7:6:5:4:3:2:1",nh=115)/Raw('\x00\x00\x03\xe8')/
     Raw('x' * 20)

Test Case: L2TPv3 with IPv4 SIP, DIP and IPv6 SIP, DIP configured together
==========================================================================

1. Stop testpmd port before loading profile::

    testpmd > port stop <port_id>

2. Set the fdir inset as follows ::

    testpmd> port config <port_id> pctype <pctype> fdir_inset clear all
    testpmd> port config <port_id> pctype <pctype> fdir_inset clear all
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 15
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 16
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 27
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 28
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 44
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 45
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 13
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 14
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 15
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 16
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 17
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 18
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 19
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 20
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 21
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 22
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 23
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 24
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 25
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 26
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 27
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 28
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 44
    testpmd> port config <port_id> pctype <pctype> fdir_inset set field 45

3. Start testpmd port ::

    testpmd> port start <port_id>

4. Start forwarding ::

    testpmd> start

5. Add l2tpv3 flow director rule,set sessionID as 1,queue 10 for IPv4 flow::

    testpmd> flow create <port_id> ingress pattern eth / ipv4 src is 10.10.10.1 dst
    is 20.10.10.20 / l2tpv3oip session_id is 1 / end actions queue index 10
    / end

6. Add l2tpv3 flow director rule, set sessionID as 1000, queue 20 for IPv6
   flow ::

    testpmd> flow create <port_id> ingress pattern eth / ipv6 src is 1:2:3:4:5:6:7:8
    ipv6 dst is 8:7:6:5:4:3:2:1 / l2tpv3oip session_id is 1000 / end actions
    queue index 20 / end

7. Send L2TPv3 IPv4 packet with SIP, DIP and session ID matching the
   configured rule, Packets should be received on queue 10::

    p=Ether()/IP(src="10.10.10.1", dst= "20.10.10.20",proto=115)/
    Raw('\x00\x00\x00\x01')/Raw('x' * 20)

8. Send L2TPv3 IPv4 packet with session ID not matching the configured rule,
   Packet should be received on queue 0::

    p=Ether()/IP(src="10.10.10.1", dst= "20.10.10.20",proto=115)/
    Raw('\x00\x00\x00\x11')/Raw('x' * 20)

9. Send L2TPv3 IPv4 packet with SIP not matching the configured rule,
   Packets should be received on queue 0::

     p=Ether()/IP(src="100.10.10.1", dst= "20.10.10.20",proto=115)/
     Raw('\x00\x00\x00\x01')/Raw('x' * 20)

10. Send L2TPv3 IPv4 packet with DIP not matching the configured rule, Packet
    should be received on queue 0::

     p=Ether()/IP(src="10.10.10.1", dst="220.10.10.20",proto=115)/
     Raw('\x00\x00\x00\x01')/Raw('x' * 20)

11. Send L2TPv3 IPv6 packet with SIP, DIP and session ID matching the
    configured rule, Packets should be received on queue 20::

     p=Ether()/IPv6(src="1:2:3:4:5:6:7:8",ipv6 dst="8:7:6:5:4:3:2:1",nh=115)/
     Raw('\x00\x00\x03\xe8')/Raw('x' * 20)

12. Send L2TPv3 IPv6 packet with session ID not matching the configured rule,
    Packet should be received on queue 0::

     p=Ether()/IPv6(src="1:2:3:4:5:6:7:8",ipv6 dst="8:7:6:5:4:3:2:1",nh=115)/
     Raw('\x00\x00\x03\xF8')/Raw('x' * 20)

13. Send L2TPv3 IPv6 packet with SIP not matching the configured rule, Packet
    should be received on queue 0::

     p=Ether()/IPv6(src="1111:2:3:4:5:6:7:8",ipv6 dst="8:7:6:5:4:3:2:1",nh=115)
     /Raw('\x00\x00\x03\xe8')/Raw('x' * 20)

14. Send L2TPv3 IPv6 packet with DIP not matching the configured rule, Packet
    should be received on queue 0::

     p=Ether()/IPv6(src="1:2:3:4:5:6:7:8",ipv6 dst="8888:7:6:5:4:3:2:1",nh=115)/
     Raw('\x00\x00\x03\xe8')/Raw('x' * 20)
