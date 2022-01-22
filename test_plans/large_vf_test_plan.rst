.. Copyright (c) <2020>, Intel Corporation
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

============================
CVL: Large VF for 256 queues
============================

Prerequisites
=============

1. Hardware:
   columbiaville_25g/columbiaville_100g

2. Software:
   DPDK: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Copy specific ice package to /lib/firmware/updates/intel/ice/ddp/ice.pkg
   Then reinstall kernel driver.

4. Generate 3 VFs on each PF and set mac address for VF0::

    echo 3 > /sys/bus/pci/devices/0000:60:00.0/sriov_numvfs

    ip link set enp96s0f0 vf 0 mac 00:11:22:33:44:55

5. Bind VF0 to vfio-pci

6. Start testpmd with "--txq=256 --rxq=256" to setup 256 queues::

    ./<build_target>/app/dpdk-testpmd -c ff -n 4 -- -i --rxq=256 --txq=256 --total-num-mbufs=500000

Note::

     Without --total-num-mbufs, may meet fail to allocate mbuf for so many queues.
     --total-num-mbufs=N, N is mbuf number, usually allocate 512 mbuf for one
     queue, if use 3 VFs, N >= 512*256*3=393216.

Test case: 3 Max VFs + 256 queues
=================================

Subcase 1 : multi fdir for 256 queues of consistent queue group
---------------------------------------------------------------

Creat rules::
    # rule 0, queue base 0, count 64
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 / end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 end / mark id 1 / end

    #rule 1, queue base 64, count 64
    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / end actions rss queues 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 end / mark id 2 / end

    #rule 2, queue base 128, count 64
    flow create 0 ingress pattern eth / ipv4 / tcp src is 22 / end actions rss queues 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 end / mark id 3 / end

    #rule 3, queue base 192, count 64
    flow create 0 ingress pattern eth / ipv6 dst is 2001::2 / tcp dst is 23 / end actions rss queues 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 214 215 216 217 218 219 220 221 222 223 224 225 226 227 228 229 230 231 232 233 234 235 236 237 238 239 240 241 242 243 244 245 246 247 248 249 250 251 252 253 254 255 end / mark id 4 / end

Send matched rule packets, check testpmd receives packets in configured queues.

Send 1000 matched IPv4 UDP packets with random IP source::

    pkt=Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x'*80)

Check the IPv4 UDP packets are redirected by RSS to queue [0~63] with FDIR matched ID=0x1.

Send 1000 matched IPv6 UDP packets with random UDP sport::

    pkt=Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::2")/UDP(sport=RandShort())/('x'*80)

Check the IPv6 UDP packets are redirected by RSS to queue [64~127] with FDIR matched ID=0x2.

Send 1000 matched IPv4 TCP packets with random TCP dport::

    pkt=Ether(dst="00:11:22:33:44:55")/IP()/TCP(sport=22, dport=RandShort())/Raw('x'*80)

Check the IPv4 TCP packets are redirected by RSS to queue [128~191] with FDIR matched ID=0x3.

Send 1000 matched IPv6 TCP packets with random TCP sport::

    pkt=Ether(dst="00:11:22:33:44:55")/IPv6(dst="2001::2")/TCP(dport=23, sport=RandShort())/Raw('x'*80)

Check the IPv6 TCP packets are redirected by RSS to queue [192~255] with FDIR matched ID=0x4.

Send mismatched rule packets, check testpmd receives packets in [0~63] queues.

Send 1000 mismatched IPv4 UDP packets with random IP source::

    pkt=Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst="192.168.0.22")/UDP(sport=22,dport=24)/Raw('x'*80)

Check the IPv4 UDP packets are redirected by RSS to queue [0~63] without FDIR matched ID=0x1.

Send 1000 matched IPv6 UDP packets with random UDP sport::

    pkt=Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::3")/UDP(sport=RandShort())/('x'*80)

Check the IPv6 UDP packets are redirected by RSS to queue [0~63] without FDIR matched ID=0x2.

Send 1000 mismatched IPv4 TCP packets with random TCP dport::

    pkt=Ether(dst="00:11:22:33:44:55")/IP()/TCP(sport=23, dport=RandShort())/Raw('x'*80)

Check the IPv4 TCP packets are redirected by RSS to queue [0~63] without FDIR matched ID=0x3.

Send 1000 mismatched IPv6 TCP packets with random TCP sport::

    pkt=Ether(dst="00:11:22:33:44:55")/IPv6(dst="2001::2")/TCP(dport=22, sport=RandShort())/Raw('x'*80)

Check the IPv6 TCP packets are redirected by RSS to queue [0~63] without FDIR matched ID=0x4.

Subcase 2 : multi fdir for 256 queues of inconsistent queue group
-----------------------------------------------------------------

Creat rules::

    # rule 0, queue base 5, count 16
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 / end actions rss queues 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 end / mark id 1 / end

    #rule 1, queue base 80, count 8
    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / end actions rss queues 80 81 82 83 84 85 86 87 end / mark id 2 / end

    #rule 2, queue base 150, count 64
    flow create 0 ingress pattern eth / ipv4 / tcp src is 22 / end actions rss queues 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 end / mark id 3 / end

    #rule 3, queue base 252, count 4
    flow create 0 ingress pattern eth / ipv6 dst is 2001::2 / tcp dst is 23 / end actions rss queues 252 253 254 255 end / mark id 4 / end

Send matched rule packets, check testpmd receives packets in configured queues.

Send 1000 matched IPv4 UDP packets with random IP source::

    pkt=Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x'*80)

Check the IPv4 UDP packets are redirected by RSS to queue [5~20] with FDIR matched ID=0x1.

Send 1000 matched IPv6 UDP packets with random UDP sport::

    pkt=Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::2")/UDP(sport=RandShort())/('x'*80)

Check the IPv6 UDP packets are redirected by RSS to queue [80~87] with FDIR matched ID=0x2.

Send 1000 matched IPv4 TCP packets with random TCP dport::

    pkt=Ether(dst="00:11:22:33:44:55")/IP()/TCP(sport=22, dport=RandShort())/Raw('x'*80)

Check the IPv4 TCP packets are redirected by RSS to queue [150~213] with FDIR matched ID=0x3.

Send 1000 matched IPv6 TCP packets with random TCP sport::

    pkt=Ether(dst="00:11:22:33:44:55")/IPv6(dst="2001::2")/TCP(dport=23, sport=RandShort())/Raw('x'*80)

Check the IPv6 TCP packets are redirected by RSS to queue [252~255] with FDIR matched ID=0x4.

Send mismatched rule packets, check testpmd receives packets in [0~63] queues.

Send 1000 mismatched IPv4 UDP packets with random IP source::

    pkt=Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst="192.168.0.22")/UDP(sport=22,dport=24)/Raw('x'*80)

Check the IPv4 UDP packets are redirected by RSS to queue [0~63] without FDIR matched ID=0x1.

Send 1000 matched IPv6 UDP packets with random UDP sport::

    pkt=Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::3")/UDP(sport=RandShort())/('x'*80)

Check the IPv6 UDP packets are redirected by RSS to queue [0~63] without FDIR matched ID=0x2.

Send 1000 mismatched IPv4 TCP packets with random TCP dport::

    pkt=Ether(dst="00:11:22:33:44:55")/IP()/TCP(sport=23, dport=RandShort())/Raw('x'*80)

Check the IPv4 TCP packets are redirected by RSS to queue [0~63] without FDIR matched ID=0x3.

Send 1000 mismatched IPv6 TCP packets with random TCP sport::

    pkt=Ether(dst="00:11:22:33:44:55")/IPv6(dst="2001::3")/TCP(dport=23, sport=RandShort())/Raw('x'*80)

Check the IPv6 TCP packets are redirected by RSS to queue [0~63] without FDIR matched ID=0x4.


Subcase 3: basic TX/RX
----------------------

Set txonly forward.

Start testpmd for several seconds.

Stop testpmd and check packet statistics, check all [0~255] queues have forwarded packet statistics.

Set rxonly forward.

Send 1000 IPv4 UDP packets with random IP source::

    pkt=Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x'*80)

Stop testpmd and check the IPv4 UDP packets are redirected by RSS to queue [0~63], max to support only 64 queues.

Subcase 4: 256 queues and 16 queues switch
------------------------------------------

Start testpmd with "--txq=256 --rxq=256".

Show port info to check queue number is 256.

Change 256 queues to 16 queues::

    port config all rxq 16
    port config all txq 16

Show port info to check queue number is 16.

Set fwd txonly to check TX could work.

Creat rules::

    #rule 0, queue base 1, count 4
    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / end actions rss queues 1 2 3 4 end / mark id 1 / end

    #rule 1, queue base 8, count 8
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 / end actions rss queues 8 9 10 11 12 13 14 15 end / mark id 2 / end

Send matched rule packets, check testpmd receives packets in configured queues.

Send 1000 matched IPv6 UDP packets with random UDP sport::

    pkt=Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::2")/UDP(sport=RandShort())/('x'*80)

Check the IPv6 UDP packets are redirected by RSS to queue [1~4] with FDIR matched ID=0x1.

Send 1000 matched IPv4 UDP packets with random IP source::

    pkt=Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x'*80)

Check the IPv4 UDP packets are redirected by RSS to queue [8~15] with FDIR matched ID=0x2.

Send mismatched rule packets, check testpmd receives packets in [0~15] queues.

Send 1000 matched IPv6 UDP packets with random UDP sport::

    pkt=Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::3")/UDP(sport=RandShort())/('x'*80)

Check the IPv6 UDP packets are redirected by RSS to queue [0~15] without FDIR matched ID=0x1.

Send 1000 mismatched IPv4 UDP packets with random IP source::

   pkt=Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst="192.168.0.22")/UDP(sport=22,dport=24)/Raw('x'*80)

Check the IPv4 UDP packets are redirected by RSS to queue [0~15] without FDIR matched ID=0x2.

Change 16 queues to 256 queues::

    port config all rxq 256
    port config all txq 256

Show port info to check queue number is 256.

Set fwd txonly to check TX could work.

Repeat subcase1 test steps.

Repeat above steps for 2 times.

Subcase 5: PF fdir + large VF fdir co-exist
-------------------------------------------

Start testpmd on VF0 with 256 queues.

Create 10 rules on PF0, queue from [54~63]::

    ethtool -N enp96s0f0 flow-type udp4 dst-ip 192.168.0.21 src-port 22 action 63
    ethtool -N enp96s0f0 flow-type udp4 dst-ip 192.168.0.22 src-port 22 action 62
    ethtool -N enp96s0f0 flow-type udp4 dst-ip 192.168.0.23 src-port 22 action 61
    ...
    ethtool -N enp96s0f0 flow-type udp4 dst-ip 192.168.0.30 src-port 22 action 54

Check rules on PF::

    ethtool -n enp96s0f0

Send matched patches to PF::

    pkt1=Ether(dst="00:00:00:00:01:00")/IP(src=RandIP(),dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x'*80)
    ......
    pkt10=Ether(dst="00:00:00:00:01:00")/IP(src=RandIP(),dst="192.168.0.30")/UDP(sport=22,dport=23)/Raw('x'*80)

Check PF matched queue [54~63] could receive matched packet::

    ethtool -S enp96s0f0

Repeat subcase1 steps to check large VF 256 queues could work.

Delete rules on PF::

    ethtool -N enp96s0f0 delete 15861

Subcase 6: negative: fail to test exceed 256 queues
---------------------------------------------------
Start testpmd on VF0 with 512 queues::

    ./<build_target>/app/dpdk-testpmd -c f -n 4 -- -i --txq=512 --rxq=512

or::
    ./<build_target>/app/dpdk-testpmd -c f -n 4 -- -i --txq=256 --rxq=256
    testpmd> port stop all
    testpmd> port config all rxq 512
    testpmd> port config all txq 512
    testpmd> port start all

Fail to setup test.


Subcase 7: negative: fail to setup 256 queues when more than 3 VFs
------------------------------------------------------------------
Create 4 VFs.
Bind all VFs to vfio-pci.
Fail to start testpmd with "--txq=256 --rxq=256".


Test case: 128 Max VFs + 4 queues (default)
===========================================

Subcase 1: multi fdir among 4 queues for 128 VFs
------------------------------------------------
Creat 128 VFs.
Bind VF0 to vfio-pci.

Create rules::

    # rule 0, queue base 0, count 2
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 / end actions rss queues 0 1 end / mark id 1 / end

    #rule 1, queue base 64, count 64
    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / end actions rss queues 2 3 end / mark id 2 / end

Send matched rule packets, check testpmd receives packets in configured queues.

Send 1000 matched IPv4 UDP packets with random IP source::

    pkt=Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x'*80)

Check the IPv4 UDP packets are redirected by RSS to queue [0~1] with FDIR matched ID=0x1.

Send 1000 matched IPv6 UDP packets with random UDP sport::

    pkt=Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::2")/UDP(sport=RandShort())/('x'*80)

Check the IPv6 UDP packets are redirected by RSS to queue [2~3] with FDIR matched ID=0x2.

Send mismatched rule packets, check testpmd receives packets in [0~3] queues.

Send 1000 mismatched IPv4 UDP packets with random IP source::

    pkt=Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(),dst="192.168.0.22")/UDP(sport=22,dport=24)/Raw('x'*80)

Check the IPv4 UDP packets are redirected by RSS to queue [0~3] without FDIR matched ID=0x1.

Send 1000 matched IPv6 UDP packets with random UDP sport::

    pkt=Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::3")/UDP(sport=RandShort())/('x'*80)

Check the IPv6 UDP packets are redirected by RSS to queue [0~3] without FDIR matched ID=0x2.

Subcase 3: negative: fail to test more than 128 VFs
---------------------------------------------------
Success to create 128 max VFs with 4 QPs per PF default::

    echo 128 > /sys/bus/pci/devices/0000\:60\:00.0/sriov_numvfs

If create 129 VFs, will report fail::

    echo 129 > /sys/bus/pci/devices/0000\:60\:00.0/sriov_numvfs
    -bash: echo: write error: Numerical result out of range

Subcase 4: negative: fail to setup more than 4 queues when VF number is 128
---------------------------------------------------------------------------

Create 128 max VFs.

Bind all VFs to vfio-pci, only have 32 ports, reached maximum number of ethernet ports.

Start testpmd with queue exceed 4 queues::

     ./<build_target>/app/dpdk-testpmd -c f -n 4 -- -i --txq=8 --rxq=8

or::

    ./<build_target>/app/dpdk-testpmd -c f -n 4 -- -i --txq=4 --rxq=4
    testpmd> port stop all
    testpmd> port config all rxq
    testpmd> port config all rxq 8
    testpmd> port config all txq 8
    testpmd> port start all

Fail to setup test.

