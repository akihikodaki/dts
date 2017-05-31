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

===================
PTYPE Mapping Tests
===================

All PTYPEs (packet types) in DPDK PMDs before are statically defined
using static constant map tables. It makes impossible to add a new
packet type without first defining them statically and then recompiling
DPDK. New NICs are flexible enough to be reconfigured depending on the
network environment. In case of FVL new PTYPEs can be added
dynamically at device initialization time using corresponding AQ
commands.
Note that the packet types of the same packet recognized by different
hardware may be different, as different hardware may have different
capabilities of packet type recognition.

This 32 bits of packet_type can be divided into several sub fields to
indicate different packet type information of a packet. The initial design
is to divide those bits into fields for L2 types, L3 types, L4 types, tunnel
types, inner L2 types, inner L3 types and inner L4 types. All PMDs should
translate the offloaded packet types into these 7 fields of information for
user applications.


Prerequisites
=============
Start testpmd, enable rxonly and verbose mode::

        ./testpmd -c f -n 4 -- -i --port-topology=chained

Test Case 1: Get ptype mapping
==============================

Get hardware defined ptype to software defined ptype mapping items::

    testpmd> ptype mapping get <port_id> <valid_only>

Note that valid_only parameter::

    (0) target represents a specific software defined ptype.
    (!0) target is a mask to represent a group of software defined ptypes.

Check the table, first column is hardware ptype, second column is software
ptype. Take hw_ptype is 24 for example::

    ...
    22     0x00000391
    23     0x00000691
    24     0x00000291
    26     0x00000191
    27     0x00000491
    ...

    [24] = RTE_PTYPE_L2_ETHER | RTE_PTYPE_L3_IPV4_EXT_UNKNOWN |
                            RTE_PTYPE_L4_UDP,

   RTE_PTYPE_L2_ETHER defined as 0x00000001,
   RTE_PTYPE_L3_IPV4_EXT_UNKNOWN defined as 0x00000090,
   RTE_PTYPE_L4_UDP defined as 0x00000200,

Calculate with L2/L3/L4 mask, we can get the ptype is 0x00000291.

1. Set <valid_only> as 0, Check that get 0~255 full columns ptype mapping
   items.

2. Set <valid_only> as 1, Check that get defined ptype mapping items.

3. Send packets, check RX dump packets software and hardware ptypes'
   correctness as below table::

    sendp([Ether()/IP()/IPv6()/UDP()/Raw('\0'*40)],iface=txItf)
    sendp([Ether()/IP()/NVGRE()/Ether()/Dot1Q()/IP()/Raw('\0'*40)],iface=txItf)

   +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+
   | Outer L2   | Outer L3         | Outer L4    | Tunnel     | Inner L2   | Inner L3         | Inner L4   | sw_ptype   | hw_ptype|
   +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | IP         | Unknown    | IPV6_EXT_UNKNOWN | UDP        | 0x02601091 |   38    |
   +------------+------------------+-------------+------------+------------+-------------------------------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | GRENAT     | ETHER_VLAN | IPV4_EXT_UNKNOWN | NONFRAG    | 0x06426091 |   75    |
   +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+

   Dumped packet::

        testpmd> port 0/queue 0: received 1 packets
          src=00:00:00:00:00:00 - dst=FF:FF:FF:FF:FF:FF - type=0x0800 -
          length=122 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN
          TUNNEL_IP INNER_L3_IPV6_EXT_UNKNOWN INNER_L4_UDP - sw ptype:
          L2_ETHER L3_IPV4 TUNNEL_IP INNER_L3_IPV6 INNER_L4_UDP  - l2_len=14
          - l3_len=20 - tunnel_len=0 - inner_l3_len=40 - inner_l4_len=8 -
          Receive queue=0x0
          ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD
          port 0/queue 0: received 1 packets
          src=00:00:00:00:00:00 - dst=FF:FF:FF:FF:FF:FF - type=0x0800 -
          length=120 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN
          TUNNEL_GRENAT INNER_L2_ETHER_VLAN INNER_L3_IPV4_EXT_UNKNOWN
          INNER_L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4 TUNNEL_NVGRE
          INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=14 - l3_len=20 -
          tunnel_len=8 - inner_l2_len=18 - inner_l3_len=20 - Receive
          queue=0x0 ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD


Test Case 2: Reset ptype mapping
================================

1. Send packet and dump RX, check outer_L2, outer_L3, outer_L4, tunnel,
   inner L2, inner L3, inner L4 as below table::

       sendp([Ether()/IP()/IPv6()/UDP()/Raw('\0'*40)],iface=txItf)

   +------------+------------------+-------------+------------+------------+------------------+----------+------------+---------+
   | Outer L2   | Outer L3         | Outer L4    | Tunnel     | Inner L2   | Inner L3         | Inner L  | sw_ptype   | hw_ptype|
   +------------+------------------+-------------+------------+------------+------------------+----------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | IP         | Unknown    | IPV6_EXT_UNKNOWN | UDP      | 0x02601091 |   38    |
   +------------+------------------+-------------+------------+------------+------------------+----------+------------+---------+

2. Check ptype mapping items: hw_ptype=38, sw_ptype=0x02601091

3. Update hardware defined ptype to software defined packet type mapping table.
   Note that hw_ptype should among 0~255, sw_ptype should conform defined mask,
   e.g. change outer L3 value to 0x000000e0, which is IPV6_EXT_UNKNOWN::

      testpmd> ptype mapping update 0 38 0x026010e1

4. Check ptype mapping hw_ptype=38 and sw_ptype is updated to 0x026010e1

5. Send packet and dump RX, check outer_L3 is changed to IPV6_EXT_UNKNOWN::

      sendp([Ether()/IP()/IPv6()/UDP()/Raw('\0'*40)],iface=txItf)

6. Reset ptype mapping table to default::

    testpmd> ptype mapping reset <port_id>

7. Check ptype mapping hw_ptype=38 and sw_ptype is updated to 0x02601091

8. Send packet and dump RX, check outer_L3 is changed to IPV4_EXT_UNKNOWN


Test Case 3: Update ptype mapping
=================================

1. Send packets and dump RX, check outer_L2, outer_L3, outer_L4, tunnel,
   inner L2, inner L3, inner L4 as below table::

      sendp([Ether()/IP()/IPv6()/UDP()/Raw('\0'*40)],iface=txItf)
      sendp([Ether()/IP()/NVGRE()/Ether()/Dot1Q()/IP()/Raw('\0'*40)],iface=txItf)

   +------------+------------------+-------------+------------+------------+------------------+-----------+------------+---------+
   | Outer L2   | Outer L3         | Outer L4    | Tunnel     | Inner L2   | Inner L3         | Inner L4  | sw_ptype   | hw_ptype|
   +------------+------------------+-------------+------------+------------+------------------+-----------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | IP         | Unknown    | IPV6_EXT_UNKNOWN | UDP       | 0x02601091 |   38    |
   +------------+------------------+-------------+------------+------------+------------------------------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | GRENAT     | ETHER_VLAN | IPV4_EXT_UNKNOWN | NONFRAG   | 0x06426091 |   75    |
   +------------+------------------+-------------+------------+------------+------------------+-----------+------------+---------+

2. Get defined ptype mapping items, check when hw_ptype=38,sw_ptype is 0x02601091,
   when hw_ptype=75, sw_ptype is 0x06426091

3. Update hardware defined ptype to software defined packet type mapping table.
   Note that hw_ptype should among 0~255, sw_ptype should conform defined mask,
   e.g. change outer L3 value to 0x000000e0, which is IPV6_EXT_UNKNOWN::

    testpmd> ptype mapping update 0 38 0x026010e1

4. Update [75]'s sw_ptype same to [38]'s sw_ptypes::

    testpmd> ptype mapping update 0 75 0x026010e1

5. Check ptype mapping items: when hw_ptype=38, sw_ptype is updated to value
   0x026010e1, when hw_ptype=75,sw_ptype is updated to value 0x026010e1

6. Send packets and dump RX, check outer_L2, outer_L3, outer_L4, tunnel,
   inner L2, inner L3, inner L4 as below table, outer_L3 is changed to
   IPV6_EXT_UNKNOWN::

     sendp([Ether()/IP()/IPv6()/UDP()/Raw('\0'*40)],iface=txItf)
     sendp([Ether()/IP()/NVGRE()/Ether()/Dot1Q()/IP()/Raw('\0'*40)],iface=txItf)

   +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+
   | Outer L2   | Outer L3         | Outer L4    | Tunnel     | Inner L2   | Inner L3         | Inner L4   | sw_ptype   | hw_ptype|
   +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+
   | ETHER      | IPV6_EXT_UNKNOWN | Unknown     | IP         | Unknown    | IPV6_EXT_UNKNOWN | UDP        | 0x026010e1 |   38    |
   +------------+------------------+-------------+------------+------------+-------------------------------+------------+---------+
   | ETHER      | IPV6_EXT_UNKNOWN | Unknown     | IP         | Unknown    | IPV6_EXT_UNKNOWN | UDP        | 0x026010e1 |   75    |
   +------------+------------------+-------------+------------+------------+-------------------------------+------------+---------+

7. Reset hardware defined ptype to software defined ptype mapping table to
   default::

    testpmd> ptype mapping reset <port_id>

8. Check ptype mapping items: when hw_ptype=38, sw_ptype is changed back to
   value 00x02601091, when hw_ptype=75, sw_ptype is changed back to 0x06426091

9. Send packet and dump RX, check outer_L2, outer_L3, outer_L4, tunnel,
   inner L2, inner L3, inner L4 as below table::

      sendp([Ether()/IP()/IPv6()/UDP()/Raw('\0'*40)],iface=txItf)
      sendp([Ether()/IP()/NVGRE()/Ether()/Dot1Q()/IP()/Raw('\0'*40)],iface=txItf)

   +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+
   | Outer L2   | Outer L3         | Outer L4    | Tunnel     | Inner L2   | Inner L3         | Inner L4   | sw_ptype   | hw_ptype|
   +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | IP         | Unknown    | IPV6_EXT_UNKNOWN | UDP        | 0x02601091 |   38    |
   +------------+------------------+-------------+------------+------------+-------------------------------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | GRENAT     | ETHER_VLAN | IPV4_EXT_UNKNOWN | NONFRAG    | 0x06426091 |   75    |
   +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+


Test Case 4: Replace ptype mapping
==================================

Replace a specific or a group of software defined ptypes with a new one::

    testpmd> ptype mapping replace <port_id> <target> <mask> <pkt_type>

Note that target is the packet type to be replaced, pkt_type is the new packet
type to overwrite, mask is defined as below::

    (0) target represents a specific software defined ptype.
    (!0) target is a mask to represent a group of software defined ptypes.

1. Send packets and dump RX, check outer_L2, outer_L3, outer_L4, tunnel,
   inner L2,inner L3, inner L4 as below table::

      sendp([Ether()/IP()/IPv6()/UDP()/Raw('\0'*40)],iface=txItf)
      sendp([Ether()/IP()/NVGRE()/Ether()/Dot1Q()/IP()/Raw('\0'*40)],iface=txItf)

   +------------+------------------+-------------+------------+------------+------------------+----------+------------+---------+
   | Outer L2   | Outer L3         | Outer L4    | Tunnel     | Inner L2   | Inner L3         | Inner L4 | sw_ptype   | hw_ptype|
   +------------+------------------+-------------+------------+------------+------------------+----------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | IP         | Unknown    | IPV6_EXT_UNKNOWN | UDP      | 0x02601091 |   38    |
   +------------+------------------+-------------+------------+------------+------------------+----------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | GRENAT     | ETHER_VLAN | IPV4_EXT_UNKNOWN | NONFRAG  | 0x06426091 |   75    |
   +------------+------------------+-------------+------------+------------+------------------+----------+------------+---------+

2. Replace a specific software defined ptypes with a new one.
   e.g. change outer_L3 from Tunnel GRENAT to IP,
   so change mask from xxxx6xxx to xxxx1xxx::

      testpmd> ptype mapping replace 0 0x06426091 0 0x06421091

3. Update [38]'s sw_ptype same to [75]'s as 0x06421091::

      testpmd> ptype mapping update 0 38 0x06421091

4. Send packet and dump RX, check outer_L2, outer_L3, outer_L4, tunnel,
   inner L2, inner L3, inner L4 as below table::

      sendp([Ether()/IP()/IPv6()/UDP()/Raw('\0'*40)],iface=txItf)
      sendp([Ether()/IP()/NVGRE()/Ether()/Dot1Q()/IP()/Raw('\0'*40)],iface=txItf)

   +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+
   | Outer L2   | Outer L3         | Outer L4    | Tunnel     | Inner L2   | Inner L3         | Inner L4   | sw_ptype   | hw_ptype|
   +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | IP         | ETHER_VLAN | IPV4_EXT_UNKNOWN | NONFRAG    | 0x06421091 |   38    |
   +------------+------------------+-------------+------------+------------+-------------------------------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | IP         | ETHER_VLAN | IPV4_EXT_UNKNOWN | NONFRAG    | 0x06421091 |   75    |
   +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+

5. Mapping table has at least two same sw_ptype 0x06421091, update a group of
   0x06421091 to 0x02601091::

      testpmd> ptype mapping replace 0 0x06421091 1 0x02601091

6. Check ptype mapping items: when hw_ptype=38, sw_ptype is updated to
   0x02601091, when hw_ptype=75, sw_ptype is updated to 0x02601091

7. Send packet and dump RX, check outer_L2, outer_L3, outer_L4, tunnel,
   inner L2, inner L3, inner L4 as below table::

       sendp([Ether()/IP()/IPv6()/UDP()/Raw('\0'*40)],iface=txItf)
       sendp([Ether()/IP()/NVGRE()/Ether()/Dot1Q()/IP()/Raw('\0'*40)],iface=txItf)

   +------------+------------------+-------------+------------+------------+------------------+-----------+------------+---------+
   | Outer L2   | Outer L3         | Outer L4    | Tunnel     | Inner L2   | Inner L3         | Inner L4  | sw_ptype   | hw_ptype|
   +------------+------------------+-------------+------------+------------+------------------+-----------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | IP         | Unknown    | IPV6_EXT_UNKNOWN | UDP       | 0x02601091 |   38    |
   +------------+------------------+-------------+------------+------------+------------------------------+------------+---------+
   | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | IP         | Unknown    | IPV6_EXT_UNKNOWN | UDP       | 0x02601091 |   75    |
   +------------+------------------+-------------+------------+------------+------------------------------+------------+---------+

8. Reset hardware defined ptype to software defined ptype mapping table to
   default::

      testpmd> ptype mapping reset <port_id>

9. Check ptype mapping items: when hw_ptype=38, sw_ptype is changed back to
   value 00x02601091, when hw_ptype=75, sw_ptype is changed back to 0x06426091

10. Send packet and dump RX, check outer_L2, outer_L3, outer_L4, tunnel,
    inner L2, inner L3, inner L4 as below table::

        sendp([Ether()/IP()/IPv6()/UDP()/Raw('\0'*40)],iface=txItf)
        sendp([Ether()/IP()/NVGRE()/Ether()/Dot1Q()/IP()/Raw('\0'*40)],iface=txItf)

    +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+
    | Outer L2   | Outer L3         | Outer L4    | Tunnel     | Inner L2   | Inner L3         | Inner L4   | sw_ptype   | hw_ptype|
    +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+
    | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | IP         | Unknown    | IPV6_EXT_UNKNOWN | UDP        | 0x02601091 |   38    |
    +------------+------------------+-------------+------------+------------+-------------------------------+------------+---------+
    | ETHER      | IPV4_EXT_UNKNOWN | Unknown     | GRENAT     | ETHER_VLAN | IPV4_EXT_UNKNOWN | NONFRAG    | 0x06426091 |   75    |
    +------------+------------------+-------------+------------+------------+------------------+------------+------------+---------+
