.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021 Intel Corporation

===================================
ICE configure QoS for vf/vsi in DCF
===================================

Description
===========

Support ETS-based QoS configuration, including Arbiters configuration (strict priority, WFQ)
and BW Allocation and limitation.
1. Add a new virtchnl capability to indicate support for QoS

2. Enable DCF to set BW limits (min, max) for DPDK AVFs and arbitration mode.
To be accomplished by way of new DCF specific virtchnl op.
a) Bandwidth limits per VF (VSI) are within the context of BW allocated for the individual TCs
at TC layer (layer 2) in the topology.  The profiles will be added at the VSI level.
b) In strict arbitration mode (vs ETS mode) a PIR can be applied to layer 2 TC nodes
by the DCF for predictable behavior.

3. Enable DPDK iAVF to query QoS capability, such as UP to TC mapping,
available BW (min, max) per TC etc. To be accomplished by way of new advance virtchnl op.

4. Enable DPDK iAVF to set TC to queue mapping, to be accomplished by way of new advance virtchnl op.

Note: The AVF inherits TCs that are configured on the PF. DCF tunes the BW allocation per TC for the target AVF.
Priority: TC7>…>TC0. TC7 has the highest priority, TC0 has the lowest priority.

QoS configuration ownership::

    --------- ---------  --------- ---------     --------- --------- --------- ---------
    | queue | | queue |  | queue | | queue | ... | queue | | queue | | queue | | queue |
    --------- ---------  --------- ---------     --------- --------- --------- ---------
        |_________|          |_________|             |_________|         |_________|
             |                    |                       |                   |
         ---------            ---------               ---------           ---------
         |  VSI0 |            |  VSI1 |      ...      |  VSI0 |           |  VSI1 |
         ---------            ---------               ---------           ---------
             |____________________|                       |___________________|
                       |                                            |
                    -------                                      -------
                    | TC0 |                  ...                 | TCn |
                    -------                                      -------
                       |____________________________________________|
                                              |
                                           --------
                                           | ROOT |
                                           --------

Prerequisites
=============

1. Hardware:
   1 port from Intel® Ethernet Network Adapter E810-CQDA2(NIC-1),
   2 ports from Intel® Ethernet Network Adapter E810-XXVDA4(NIC-2);
   one 100G cable, one 10G cable;
   The connection is as below table::

    +---------------------------------+
    |  DUT           |  IXIA          |
    +=================================+
    |               100G              |
    | NIC-1,Port-1  ---  IXIA, Port-1 |
    |               10G               |
    | NIC-2,Port-1  ---  NIC-2,Port-2 |
    +---------------------------------+

   Assume that device ID and pci address of NIC-1,Port-1 are ens785f0 and 18:00.0,
   device ID and pci address of NIC-2,Port-1 are ens802f0 and 86:00.0.

2. Software:

   - dpdk: http://dpdk.org/git/dpdk
   - runtime command: https://doc.dpdk.org/guides/testpmd_app_ug/testpmd_funcs.html
   - lldptool: install the tool to configure DCB::

        apt install lldpad

   or::

        yum install lldpad

3. Don't allow the peer port modify the DCB parameter::

    lldptool -T -i ens802f0 -V ETS-CFG willing=no
    lldptool -T -i ens785f0 -V ETS-CFG willing=no

4. Configure DCB TC bandwidth with lldp tool::

    lldptool -T -i enp785s0f0 -V ETS-CFG willing=no tsa=0:strict,1:strict,2:strict,3:strict,4:strict,5:strict,6:strict,7:strict up2tc=0:0,1:0,2:0,3:1,4:2,5:0,6:0,7:0 tcbw=10,30,60,0,0,0,0,0

   Or configure DCB with dcbgetset tool(an internal tool to set DCB without peer negotiation)::

    ./dcbgetset enp785s0f0 --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0

5. Generate 2 VFs on NIC-1,Port-1 and NIC-2,Port-1::

    echo 2 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
    echo 2 > /sys/bus/pci/devices/0000:86:00.0/sriov_numvfs

6. Set each VF0 as trust mode and set each VF1 mac address::

    ip link set dev ens785f0 vf 0 trust on
    ip link set ens785f0 vf 1 mac 00:11:22:33:44:55
    ip link set dev ens802f0 vf 0 trust on
    ip link set ens802f0 vf 1 mac 00:11:22:33:44:66

7. Bind VFs to dpdk driver::

    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0 0000:18:01.1 0000:86:01.0 0000:86:01.1
    ./usertools/dpdk-devbind.py -s
    0000:18:01.0 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf
    0000:18:01.1 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf
    0000:86:01.0 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf
    0000:86:01.1 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf

8. When choose 100G testpmd setting, just use 100G NIC port, launch testpmd as below::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -- -i --txq=8 --rxq=8 --nb-cores=8 --port-topology=loop

   When choose 10G testpmd setting, use 100G NIC and 25G NIC ports, launch testpmd as below::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -a 86:01.0,cap=dcf -a 86:01.1 -- -i --txq=8 --rxq=8 --nb-cores=8

Test case 1: strict mode, check peak_tb_rate
============================================
Note: In strict mode, the "--tcbw" parameter is invalid.
The throughput is only limited by shaper profile,
and the TC priority follows the default order.
This case is to check the max rate of node limited by peak_tb_rate,
when the scheduler use strict priority mode in different user priority.

1. DCB setting, set 3 TCs bandwidth with strict mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0   
    ifconfig ens785f0 up

2. Start testpmd with 100G setting, then set profile and TC mapping::

    port stop all
    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0    
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0    
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0     
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0  

    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0       
    add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0       
    add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0          
    port tm hierarchy commit 0 no

    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 no
    port start all
    set fwd mac
    start

3. Since configured 3 TCs, send four streams from IXIA,
   mac address is vf1's mac address: "00:11:22:33:44:55", vlan=0, user priority=2,5,3,4,
   user priority 2/5 map to TC0, 3 maps to TC1, 4 maps TC2.
   frame size is 68 bytes(4 bytes vlan field added to 64 bytes packet), each stream desired 25% max rate(100Gbps).
   send each stream separately, check the TX throughput of each priority and queue mapping:
   user priority=2, throughput is 2MBps, mapping to queue0-3;
   user priority=5, throughput is 2MBps, mapping to queue0-3;
   user priority=3, throughput is 4MBps, mapping to queue4-5;
   user priority=4, throughput is 4MBps, mapping to queue6-7;
   send the four streams synchronously, the sum of throughput is 10MBps.
   and the queue mapping is correct, which is as the mapping of step3.

4. Restart testpmd, and map all the queues to 2 TCs(TC0 and TC1)::

    port stop all
    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0     
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0  
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0       
    add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0       
    add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0          
    port tm hierarchy commit 0 no
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 no
    port start all
    set fwd mac
    start

5. Send the same four streams as step3.
   send each stream separately, check the TX throughput of each priority and queue mapping:
   stream 4 are dropped by vf1.
   user priority=2, throughput is 2MBps, mapping to queue0-3;
   user priority=5, throughput is 2MBps, mapping to queue0-3;
   user priority=3, throughput is 4MBps, mapping to queue4-7;
   user priority=4, throughput is 0, no mapping queues.
   send the four streams synchronously, the sum of throughput is 6MBps.
   and the queue mapping is correct.

Test case 2: ets mode, check peak_tb_rate
=========================================
Note: In ETS mode, the "--tcbw" parameter is valid.
The throughput is only limited by TC bandwidth distribution and shaper profile,
and the TC priority follows the value of the "--tcbw" setting.
This case is to check the max rate of node limited by tcbw distribution and peak_tb_rate,
when the scheduler use ETS mode in different user priority.

1. DCB setting, set 2 TCs bandwidth with ets mode::

    ./dcbgetset ens785f0 --ieee --up2tc 0,0,0,0,1,1,1,1 --tcbw 20,80,0,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0   
    ./dcbgetset ens802f0 --ieee --up2tc 0,0,0,0,1,1,1,1 --tcbw 20,80,0,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0   
    ifconfig ens785f0 up
    ifconfig ens802f0 up

2. Start testpmd with 10G setting, then set profile and TC mapping::

    set portlist 0,2,1,3
    show config fwd
    port stop all
    add port tm node shaper profile 0 1 10000000 0 4000000000 0 0 0    
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0     
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 2 800 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 0 3 800 0 1 2 1 0 0xffffffff 0 0   
    port tm hierarchy commit 0 yes
    add port tm node shaper profile 2 1 10000000 0 1000000000 0 0 0  
    add port tm nonleaf node 2 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 2 900 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 2 800 1000 0 1 1 -1 1 0 0   
    add port tm leaf node 2 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 2 1 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 2 2 800 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 2 3 800 0 1 2 1 0 0xffffffff 0 0        
    port tm hierarchy commit 2 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    add port tm nonleaf node 3 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 3 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 3 800 1000 0 1 1 0 1 0 0
    add port tm leaf node 3 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 6 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 7 800 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 3 yes
    port start all
    set fwd mac
    start

3. Send two streams from IXIA, vlan=0, priority=0/4(TC0/TC1),
   mac address is VF1's mac address "00:11:22:33:44:55",
   frame size is 68 bytes(4 bytes vlan field added to 64 bytes packet), each stream desired 50% max rate(100Gbps).
   send each stream separately, check the port3(VF1 of 25G port) stats:
   each tx rate is about 7.3Gbps(linerate);
   stop forward, check queue mapping:
   when send stream of UP=0, the tx queues are queue0-queue3;
   when send stream of UP=4, the tx queues are queue4-queue7;
   send 2 streams synchronously, each 50%max,
   check the port3 stats, the tx rate is about 7.3Gbps,
   stop forward, check the result:
   the throughput's proportion of queue0-3 and queue4-7 is about 20:80 as the DCB TC bandwidth setting.

4. Set both two profiles' PIR to 500000000, other settings are the same as step2,
   send same streams as step3.
   send each stream separately, check the port3 tx rate is about 3.95Gbps, closed to the PIR 4Gbps,
   check queue mapping is same as step3.
   Send the two streams synchronously, the throughput is limited by the cable about 7.3Gbps.
   check the port3 stats, the tx rate is still about 7.3Gbps,
   stop forward, check the result, queue0-queue3 map TC0, queue4-queue7 map TC1
   TC0’s rate is about 3.34Gbps, TC1’s rate is about 3.95Gbps.
   the two stream’s occupation is more than 20:80, about 45:55.
   because TC1 throughput is limited by PIR, so the rest throughput is occupied by TC0.

Test case 3: strict mode, check cmit_tb_rate
============================================
This case is to check the guaranteed rate of node set by cmit_tb_rate.
Note: now, the cmit_tb_rate setting can't take work, it is not supported by kernel.

1. DCB setting, set 2 TCs bandwidth with strict mode::

    ./dcbgetset ens785f0 --ieee --up2tc 0,0,0,1,0,0,0,0 --tcbw 10,90,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0
    ./dcbgetset ens802f0 --ieee --up2tc 0,0,0,1,0,0,0,0 --tcbw 10,90,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0
    ifconfig ens785f0 up
    ifconfig ens802f0 up

2. Start testpmd with 10G setting, then set profile and TC mapping as test_case 2 step2.

3. Send two streams from IXIA,
   mac address is VF1's mac address "00:11:22:33:44:55", vlan=0, priority=0/3(TC0/TC1),
   frame size is 68 bytes(4 bytes vlan field added to 64 bytes packet), each stream desired 50% max rate.
   send each stream separately, check the port3(VF1 of 25G port) tx rate is about 7.3Gbps,
   check queue mapping is same as test_case 2 step3.
   send 2 streams synchronously, each 50%max
   check the port3 stats, the tx rate is about 7.3Gbps,
   stop forward, check the result,
   queue0-queue3 which mapping to TC0 should have 80Mbps rate
   queue4-queue7 which mapping to TC1 have about 7.22Gbps.

Note: the cmit of the profile is not supported now, so the current expected result is:
   all the TX throughput should at TC1, TC0 should has no throughput.
   queue0-queue3 which mapping to TC0 have no throughput
   queue4-queue7 which mapping to TC1 have about 7.3Gbps.


Test case 4: ets mode, check the TC throughput of min BW allocation
===================================================================
this case is to check the TC throughput of min BW allocation.

1. DCB setting, set 3 TCs bandwidth with ets mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,0,1,1,2,2,2,2 --tcbw 1,10,89,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0
    ./dcbgetset ens802f0  --ieee --up2tc 0,0,1,1,2,2,2,2 --tcbw 1,10,89,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0
    ifconfig ens785f0 up
    ifconfig ens802f0 up

2. start testpmd with 10G setting::

    set portlist 0,2,1,3
    show config fwd
    port stop all
    add port tm node shaper profile 0 1 1000000000 0 4000000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 3 800 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 5 700 0 1 2 1 0 0xffffffff 0 0
    port tm hierarchy commit 0 yes
    add port tm node shaper profile 2 1 100000000 0 1000000000 0 0 0
    add port tm node shaper profile 2 2 100000000 0 150000000 0 0 0
    add port tm nonleaf node 2 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 2 900 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 2 800 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 2 700 1000 0 1 1 -1 1 0 0
    add port tm leaf node 2 0 900 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 2 1 900 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 2 2 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 2 3 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 2 4 700 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 2 5 700 0 1 2 1 0 0xffffffff 0 0
    port tm hierarchy commit 2 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    add port tm nonleaf node 3 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 3 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 3 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 3 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 3 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 2 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 3 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 6 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 7 700 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 3 yes
    port start all
    set fwd mac
    start

3. Send 8 streams from IXIA, vlan=0, priority=0-7(TC0-TC7),
   mac address is VF1's mac address "00:11:22:33:44:55",
   frame size is 1024 bytes, each stream desired 12.5% max rate.
   send each stream separately, the PIR can be reached, and the queue mapping is correct:
   UP0(TC0) stream maps queue0-1, the throughput is 1.2Gbps.
   UP1(TC0) stream maps queue0-1, the throughput is 1.2Gbps.
   UP2(TC1) stream maps queue2-5, the throughput is 1.2Gbps.
   UP3(TC1) stream maps queue2-5, the throughput is 1.2Gbps.
   UP4(TC2) stream maps queue6-7, the throughput is 8Gbps.
   UP5(TC2) stream maps queue6-7, the throughput is 8Gbps.
   UP6(TC2) stream maps queue6-7, the throughput is 8Gbps.
   UP7(TC2) stream maps queue6-7, the throughput is 8Gbps.
   send 8 streams synchronously, check throughput is 9.77Gbps,
   TC2 and TC1's PIR(1.2Gbps/8Gbps) can be satisfied, and the rest rate is given to TC0.

4. Set frame size to 68bytes, send 8 streams synchronously,
   check the throughput is about 7.273Gbps. all the TC can’t reach PIR.
   TC0 rate is 0.072Gbps, occupys 0.01 ets BW.
   TC1 rate is 0.72Gbps, occupys 0.1 ets BW.
   TC2 rate is 6.48Gbps, occupys 0.89 ets BW.
   The TC0-TC2’s rate occupation is same as bandwidth allocation: 1:10:89.

Test case 5: 2 iavf VFs, strict mode, check peak_tb_rate
========================================================
Each VF's max rate is limited by the sum of peak_tb_rate of all TCs binded to it.

1. DCB setting, set 3 TCs bandwidth with strict mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0

2. Create 3 VFs::

    echo 3 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1 18:01.2
    ip link set dev ens785f0 vf 0 trust on
    ip link set ens785f0 vf 1 mac 00:11:22:33:44:55
    ip link set ens785f0 vf 2 mac 00:11:22:33:44:66

3. Start testpmd with 100G setting, different vsi node of same TC node use different profiles::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -a 18:01.2 -a 18:01.3 -- -i --txq=8 --rxq=8 --port-topology=loop --nb-cores=8
    port stop all
    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0    
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0    
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0     
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0  
    add port tm leaf node 0 0 900 0 1 2 -1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0   
    add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0           
    add port tm leaf node 0 3 800 0 1 2 -1 0 0xffffffff 0 0       
    add port tm leaf node 0 4 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 5 800 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 6 700 0 1 2 -1 0 0xffffffff 0 0       
    add port tm leaf node 0 7 700 0 1 2 1 0 0xffffffff 0 0          
    add port tm leaf node 0 8 700 0 1 2 2 0 0xffffffff 0 0          
    port tm hierarchy commit 0 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    add port tm nonleaf node 2 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 2 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 2 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 2 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 2 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 2 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 3 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 6 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 7 700 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 2 yes
    port start all
    set fwd mac
    start

4. Send 8 streams, stream0-3’s mac address is vf1's, vlan=0, priority=1/2/3/4(TC0/TC0/TC1/TC2),
   stream4-7' mac address is vf2's, vlan=0, priority=1,2,3,4,
   send each stream separately, check the stats:
   stream0 maps queue0-1 of port 1, the throughput reaches PIR of profile 1(16Mbps).
   stream1 maps queue0-1 of port 1, the throughput reaches PIR of profile 1(16Mbps).
   stream2 maps queue2-3 of port 1, the throughput reaches PIR of profile 2(32Mbps).
   stream3 maps queue4-7 of port 1, the throughput reaches PIR of profile 1(16Mbps).
   stream4 maps queue0-1 of port 2, the throughput reaches PIR of profile 1(16Mbps).
   stream5 maps queue0-1 of port 2, the throughput reaches PIR of profile 1(16Mbps).
   stream6 maps queue2-5 of port 2, the throughput reaches PIR of profile 1(16Mbps).
   stream7 maps queue6-7 of port 2, the throughput reaches PIR of profile 2(32Mbps).
   send all streams synchronously, each 12.5%max, check the sum of throughput reach 128Mbps.
   each stream's queue mapping is correct,which is same as sent separately.

Test case 6: 2 iavf VFs, strict mode, check cmit_tb_rate
========================================================
Each VF's guaranteed rate is set by the cmit_tb_rate of TC0 binded to it.
Note: now, the cmit_tb_rate setting can't take work, it is not supported by kernel.

1. DCB setting, set 3 TCs bandwidth with strict mode::

    ./dcbgetset ens785f0 --ieee --up2tc 0,0,0,1,0,0,0,0 --tcbw 20,80,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0
    ./dcbgetset ens802f0 --ieee --up2tc 0,0,0,1,0,0,0,0 --tcbw 20,80,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0

2. Create 3 VFs on each pf::

    echo 3 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    ip link set dev ens785f0 vf 0 trust on
    ip link set ens785f0 vf 1 mac 00:11:22:33:44:55
    ip link set ens785f0 vf 2 mac 00:11:22:33:44:66
    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1 18:01.2
    echo 3 > /sys/bus/pci/devices/0000\:86\:00.0/sriov_numvfs
    ip link set dev ens802f0 vf 0 trust on
    ip link set ens802f0 vf 1 mac 00:11:22:33:44:77
    ip link set ens802f0 vf 2 mac 00:11:22:33:44:88
    ./usertools/dpdk-devbind.py -b vfio-pci 86:01.0 86:01.1 86:01.2

3. Start testpmd with 10G setting::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -a 18:01.2 -a 86:01.0,cap=dcf -a 86:01.1 -a 86:01.2 -- -i --txq=8 --rxq=8 --nb-cores=8
    set portlist 0,3,1,4,2,5
    show config fwd
    port stop all
    add port tm node shaper profile 0 1 100000000 0 4000000000 0 0 0    
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0     
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0  
    add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0             
    add port tm leaf node 0 3 800 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 0 4 800 0 1 2 1 0 0xffffffff 0 0   
    add port tm leaf node 0 5 800 0 1 2 1 0 0xffffffff 0 0   
    port tm hierarchy commit 0 no
    add port tm node shaper profile 3 1 100000000 0 500000000 0 0 0  
    add port tm nonleaf node 3 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 3 900 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 3 800 1000 0 1 1 -1 1 0 0   
    add port tm leaf node 3 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 3 1 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 3 2 900 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 3 3 800 0 1 2 1 0 0xffffffff 0 0     
    add port tm leaf node 3 4 800 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 3 5 800 0 1 2 1 0 0xffffffff 0 0     
    port tm hierarchy commit 3 no
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 no
    add port tm nonleaf node 4 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 4 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 4 800 1000 0 1 1 0 1 0 0
    add port tm leaf node 4 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 6 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 7 800 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 4 no
    add port tm nonleaf node 2 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 2 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 2 800 1000 0 1 1 0 1 0 0
    add port tm leaf node 2 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 2 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 3 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 6 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 7 800 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 2 no
    add port tm nonleaf node 5 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 5 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 5 800 1000 0 1 1 0 1 0 0
    add port tm leaf node 5 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 2 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 3 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 6 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 7 800 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 5 no
    port start all
    set fwd mac
    start

4. Send 4 streams synchronously, stream0-1's mac address is vf1's, vlan id=0, UP=2/3(TC0/TC1),
   streams2-3's mac address is vf2's, vlan id=0, UP=2/3(TC0/TC1),
   frame size is 68 bytes, each stream allocates 25%max.
   check the vf4 and vf5 stats, the sum of tx rate is 7.27Gbps, each vf tx is 3.64Gbps.
   in each vf, TC0 should occupied 0.8Gbps, the rest of throughput is occupied by TC1, which is about 2.84Gbps
   stop the fwd, check each queue's tx stats,
   vf4's queue0-queue3 and vf5's queue0-queue1 map to TC0, which occupied 0.8Gbps,
   vf4's queue4-queue7 and vf5's queue2-queue7 map to TC1, which occupied 2.84Gbps.

Note: now, the cmit_tb_rate setting can't take work, it is not supported by kernel.
   So the current result of step4 should be:
   all the TX throughput are occupied by TC1, TC0 should have no throughput.
   vf4's queue0-queue3 and vf5's queue0-queue1 map to TC0, which have no throughput.
   vf4's queue4-queue7 and vf5's queue2-queue7 map to TC1, which occupied 3.64Gbps.

Test case 7: 2 iavf VFs, ets mode
=================================
In ETS mode, calculate the sum value of different vf node which binded to same TC,
the proportion of the value of different TC is consistent to TC bandwitch distribution

1. DCB setting, set 3 TCs bandwidth with ets mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0   
    ./dcbgetset ens802f0  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0   

2. Create 3 VFs on each pf::

    echo 3 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    ip link set dev ens785f0 vf 0 trust on
    ip link set ens785f0 vf 1 mac 00:11:22:33:44:55
    ip link set ens785f0 vf 2 mac 00:11:22:33:44:66
    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1 18:01.2
    echo 3 > /sys/bus/pci/devices/0000\:86\:00.0/sriov_numvfs
    ip link set dev ens802f0 vf 0 trust on
    ip link set ens802f0 vf 1 mac 00:11:22:33:44:77
    ip link set ens802f0 vf 2 mac 00:11:22:33:44:88
    ./usertools/dpdk-devbind.py -b vfio-pci 86:01.0 86:01.1 86:01.2

3. Start testpmd with 10G setting::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -a 18:01.2 -a 86:01.0,cap=dcf -a 86:01.1 -a 86:01.2 -- -i --txq=8 --rxq=8 --nb-cores=8
    set portlist 0,3,1,4,2,5
    show config fwd
    port stop all
    add port tm node shaper profile 0 1 0 0 0 0 0 0    
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0     
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0     
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0   
    add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0           
    add port tm leaf node 0 3 800 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 0 4 800 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 5 800 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 6 700 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 0 7 700 0 1 2 1 0 0xffffffff 0 0          
    add port tm leaf node 0 8 700 0 1 2 1 0 0xffffffff 0 0          
    port tm hierarchy commit 0 yes
    add port tm node shaper profile 3 1 0 0 0 0 0 0  
    add port tm nonleaf node 3 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 3 900 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 3 800 1000 0 1 1 -1 1 0 0   
    add port tm nonleaf node 3 700 1000 0 1 1 -1 1 0 0   
    add port tm leaf node 3 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 3 1 900 0 1 2 1 0 0xffffffff 0 0   
    add port tm leaf node 3 2 900 0 1 2 1 0 0xffffffff 0 0           
    add port tm leaf node 3 3 800 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 3 4 800 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 3 5 800 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 3 6 700 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 3 7 700 0 1 2 1 0 0xffffffff 0 0          
    add port tm leaf node 3 8 700 0 1 2 1 0 0xffffffff 0 0          
    port tm hierarchy commit 3 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    add port tm nonleaf node 2 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 2 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 2 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 2 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 2 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 2 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 3 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 6 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 2 7 700 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 2 yes
    add port tm nonleaf node 4 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 4 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 4 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 4 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 4 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 2 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 3 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 4 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 5 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 6 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 4 7 700 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 4 yes
    add port tm nonleaf node 5 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 5 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 5 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 5 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 5 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 2 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 3 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 6 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 5 7 700 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 5 yes
    port start all
    set fwd mac
    start

4. Send 8 streams synchronously, stream0-3’s mac address is vf1's, vlan=0, priority=1/2/3/4(TC0/TC0/TC1/TC2),
   stream4-7’s mac address is vf2's, vlan=0, priority=1/2/3/4(TC0/TC0/TC1/TC2),
   frame size 68 bytes, each stream allocates 12.5%max.
   calculate the sum of vf1 and vf2 tx rate which belongs to TC0, mark it as t0,
   calculate the sum of vf1 and vf2 tx rate which belongs to TC1, mark it as t1,
   calculate the sum of vf1 and vf2 tx rate which belongs to TC2, mark it as t2,
   check the proportion of t0:t1:t2 is 1:3:6, which can match the ets bandwidth limit 1:3:6,
   and the queue mapping is:
   stream1 maps queue0-1 of vf1,
   stream2 maps queue0-1 of vf1,
   stream3 maps queue2-3 of vf1,
   stream4 maps queue4-7 of vf1,
   stream5 maps queue0-1 of vf2,
   stream6 maps queue0-1 of vf2,
   stream7 maps queue2-5 of vf2,
   stream8 maps queue6-7 of vf2.

Test case 8: strict mode, 8 TCs
===============================
This case is to check QoS Tx side processing with max TC number set in strict priority mode.

1. DCB setting, set 8 TCs bandwidth with strict mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,1,2,3,4,5,6,7 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0

2. Start testpmd with 100G setting::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -- -i --txq=8 --rxq=8 --port-topology=loop --nb-cores=8
    port stop all
    add port tm node shaper profile 0 1 1000000 0 400000000 0 0 0
    add port tm node shaper profile 0 2 1000000 0 200000000 0 0 0
    add port tm node shaper profile 0 3 1000000 0 100000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 600 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 500 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 400 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 300 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 200 1000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 1 900 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 2 800 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 3 800 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 5 700 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 6 600 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 7 600 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 8 500 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 9 500 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 10 400 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 11 400 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 12 300 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 13 300 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 14 200 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 15 200 0 1 2 1 0 0xffffffff 0 0
    port tm hierarchy commit 0 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 600 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 500 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 400 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 300 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 200 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 600 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 500 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 400 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 300 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 200 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    port start all
    set fwd mac
    start

3. Send 8 streams synchronously, vlan id=0, UP0-UP7，68bytes, each stream 12.5%max, which is much more than PIR.
   check tx is limited by PIR, each TC can reach to PIR.

4. Change the shaper profile::

    port stop all
    add port tm node shaper profile 0 1 1000000 0 1780000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0     
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0  
    add port tm nonleaf node 0 600 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 0 500 1000 0 1 1 -1 1 0 0     
    add port tm nonleaf node 0 400 1000 0 1 1 -1 1 0 0  
    add port tm nonleaf node 0 300 1000 0 1 1 -1 1 0 0     
    add port tm nonleaf node 0 200 1000 0 1 1 -1 1 0 0  
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 2 800 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 0 3 800 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 0 5 700 0 1 2 1 0 0xffffffff 0 0          
    add port tm leaf node 0 6 600 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 7 600 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 0 8 500 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 9 500 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 0 10 400 0 1 2 1 0 0xffffffff 0 0          
    add port tm leaf node 0 11 400 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 0 12 300 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 13 300 0 1 2 1 0 0xffffffff 0 0       
    add port tm leaf node 0 14 200 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 15 200 0 1 2 1 0 0xffffffff 0 0          
    port tm hierarchy commit 0 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 600 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 500 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 400 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 300 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 200 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 600 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 500 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 400 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 300 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 200 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    port start all
    set fwd mac
    start

5. Send 8 streams synchronously, vlan id=0, UP0-UP7, 68bytes, each stream 12.5%max, which is less than PIR.
   stop the forward, check all the Tx packet drop is at queue0, which maps to TC0.
   the throughput satisfy TC7-TC1 by priority.

6. Send 8 streams synchronously, vlan id=0, UP0-UP7，1024bytes, each stream 12.5%max, which is less than PIR.
   stop the forward, check all the Tx packet drop is at queue0, which maps to TC0.
   the throughput satisfy TC7-TC1 by priority.

Test case 9: strict mode, 1 TC
==============================
This case is to check QoS Tx side processing with min TC number set in strict priority mode.

1. DCB setting, set 1 TC bandwidth with strict mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,0,0,0,0,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0

2. Start testpmd with 100G setting::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -- -i --txq=8 --rxq=8 --port-topology=loop --nb-cores=8
    port stop all
    add port tm node shaper profile 0 1 1000000 0 1000000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0
    port tm hierarchy commit 0 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 900 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    port start all
    set fwd mac
    start

3. Send 8 streams synchronously, vlan id=0, UP0-UP7, which all map to TC0, 68bytes, each stream 12.5%max.
   check the sum of Tx throughput can reach PIR(8Gbps).
   only send 1 stream, check the Tx throughput can reach PIR(8Gbps) too.

Test case 10: ets mode, 8 TCs
=============================
This case is to check QoS Tx side processing with max TC number set in ETS mode.

1. DCB setting, set 8 TCs bandwidth with ets mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,1,2,3,4,5,6,7 --tcbw 5,10,15,10,20,1,30,9 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0   
    ./dcbgetset ens802f0  --ieee --up2tc 0,1,2,3,4,5,6,7 --tcbw 5,10,15,10,20,1,30,9 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0   

2. Start testpmd with 10G setting::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -a 86:01.0,cap=dcf -a 86:01.1 -- -i --txq=8 --rxq=8 --nb-cores=8
    set portlist 0,2,1,3
    show config fwd
    port stop all
    add port tm node shaper profile 0 1 1000000 0 4000000000 0 0 0
    add port tm node shaper profile 0 2 1000000 0 2000000000 0 0 0
    add port tm node shaper profile 0 3 1000000 0 1000000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 600 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 500 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 400 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 300 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 200 1000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 1 900 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 2 800 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 3 800 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 5 700 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 6 600 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 7 600 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 8 500 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 9 500 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 0 10 400 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 11 400 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 12 300 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 13 300 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 14 200 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 15 200 0 1 2 1 0 0xffffffff 0 0
    port tm hierarchy commit 0 yes
    add port tm node shaper profile 2 1 1000000 0 400000000 0 0 0
    add port tm node shaper profile 2 2 1000000 0 200000000 0 0 0
    add port tm node shaper profile 2 3 1000000 0 100000000 0 0 0
    add port tm nonleaf node 2 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 2 900 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 2 800 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 2 700 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 2 600 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 2 500 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 2 400 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 2 300 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 2 200 1000 0 1 1 -1 1 0 0
    add port tm leaf node 2 0 900 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 2 1 900 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 2 2 800 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 2 3 800 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 2 4 700 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 2 5 700 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 2 6 600 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 2 7 600 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 2 8 500 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 2 9 500 0 1 2 3 0 0xffffffff 0 0
    add port tm leaf node 2 10 400 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 2 11 400 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 2 12 300 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 2 13 300 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 2 14 200 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 2 15 200 0 1 2 1 0 0xffffffff 0 0
    port tm hierarchy commit 2 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 600 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 500 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 400 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 300 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 200 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 600 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 500 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 400 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 300 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 200 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    add port tm nonleaf node 3 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 3 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 3 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 3 700 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 3 600 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 3 500 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 3 400 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 3 300 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 3 200 1000 0 1 1 0 1 0 0
    add port tm leaf node 3 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 1 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 2 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 3 600 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 4 500 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 5 400 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 6 300 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 7 200 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 3 yes
    port start all
    set fwd mac
    start

3. Send 8 streams synchronously, vlan id=0, UP0-UP7, which map TC0-TC7, 68bytes, each stream 12.5%max,
   check port3 stats, the Tx rate is 7.3Gbps.
   stop forward, check the tx rate, queue0-queue4 correspond to TC0-TC4, can reach the PIR(100MBps),
   queue6 which corresponds to TC6 is limited by PIR(200MBps) too.
   queue7(maps to TC7) is limited by Rx IXIA traffic, can’t reach PIR(400MBps),
   and queue5(maps to TC5) is the lowest priority, other TCs must be satisfied first,
   so TC5 and TC7 are limited by the bandwidth distribution 1:9.

4. Set profile of port2 as below::

    add port tm node shaper profile 2 1 1000000 0 100000000 0 0 0    
    add port tm node shaper profile 2 2 1000000 0 250000000 0 0 0    
    add port tm node shaper profile 2 3 1000000 0 100000000 0 0 0    

   Send the same 8 streams synchronously,
   check port3 stats, the Tx rate is 7.3Gbps.
   stop forward, check the tx rate, queue0-queue4 and queue6-7 can reach PIR(are limited by PIR),
   queue5(corresponds to TC5) is the lowest priority (1% BW set by DCB), 
   the rest rate are put to queue 5, may be more than 1% of whole throughput.

5. Set all the profile PIR=0::

    add port tm node shaper profile 2 1 0 0 0 0 0 0    
    add port tm node shaper profile 2 2 0 0 0 0 0 0    
    add port tm node shaper profile 2 3 0 0 0 0 0 0    

   Send the same 8 streams synchronously,
   check port3 stats, the Tx rate is 7.3Gbps.
   check all the steam's tx throughput proportion is due to ets bandwidth distribution(5:10:15:10:20:1:30:9).

Test case 11: ets mode, 1 TC
============================
This case is to check QoS Tx side processing with min TC number set in ETS mode.

1. DCB setting, set 1 TC bandwidth with ets mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,0,0,0,0,0,0,0 --tcbw 100,0,0,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0   
    ./dcbgetset ens802f0  --ieee --up2tc 0,0,0,0,0,0,0,0 --tcbw 100,0,0,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0   

2. Start testpmd with 10G setting::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -a 86:01.0,cap=dcf -a 86:01.1 -- -i --txq=8 --rxq=8 --nb-cores=8
    set portlist 0,2,1,3
    show config fwd
    port stop all
    add port tm node shaper profile 0 1 1000000 0 10000000000 0 0 0    
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0    
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0        
    port tm hierarchy commit 0 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 900 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    add port tm node shaper profile 2 1 1000000 0 1000000000 0 0 0    
    add port tm nonleaf node 2 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 2 900 1000 0 1 1 -1 1 0 0    
    add port tm leaf node 2 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 2 1 900 0 1 2 1 0 0xffffffff 0 0        
    port tm hierarchy commit 2 yes
    add port tm nonleaf node 3 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 3 900 1000 0 1 1 0 1 0 0
    add port tm leaf node 3 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 4 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 5 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 6 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 3 7 900 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 3 yes
    port start all
    set fwd mac
    start

3. Send 8 streams synchronously, vlan id=0, UP0-UP7, 68bytes, each stream 12.5%max.
   check the sum of Tx throughput can reach 7.3Gbps.
   only send 1 stream, check the Tx throughput can reach 7.3Gbps too.

Test case 12: query qos setting
===============================
The case is to check the support to query QoS settings.

1. DCB setting, set 3 TCs bandwidth with strict mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0
    ifconfig ens785f0 up

2. Start testpmd with 100G setting, then set profile and TC mapping::

    port stop all
    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0    
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0   
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0  
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0     
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0     
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0       
    add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0  
    add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0       
    add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0  
    port tm hierarchy commit 0 no
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 no
    port start all

3. Show port tm capability::

    show port tm cap 1

   Show port tm level capability::

    show port tm level cap 1 0
    show port tm level cap 1 1
    show port tm level cap 1 2

   Check shaper_private_rate_max are the same::

    shaper_private_rate_max 12500000000

   The value is speed of the port.
   The shaper_private_rate_min is 0.

   Show port tm node capability::

    show port tm node cap 1 900
    show port tm node cap 1 800

   Check shaper_private_rate_max and shaper_private_rate_min,
   the TC node value is consistent to profile setting.
   node 900::

    cap.shaper_private_rate_min 1000000
    cap.shaper_private_rate_max 2000000

   node 800::

    cap.shaper_private_rate_min 1000000
    cap.shaper_private_rate_max 4000000

   Check all the unit of rate is consistent which is Bps.
   Show capability of node 0-7 for port 1::

    show port tm node cap 1 1
    node parameter null: not support capability get (error 22)

   It's not supported by queue node.

4. Show port tm node type::

    show port tm node type 1 0
    show port tm node type 1 900
    show port tm node type 1 1000

   The result is::

    leaf node
    nonleaf node
    nonleaf node

   Check the type is correct.

Test case 13: pf reset
======================
This case is to check if the QoS setting works after resetting PF.

1. Run the test case 1, the result is as expected.

2. Reset pf::

    echo 1 > /sys/devices/pci0000:17/0000:17:00.0/0000:18:00.0/reset

3. Send same streams as step1, check no packets received and transmitted.

Test case 14: vf reset
======================
This case is to check if the QoS setting works after resetting VF.

1. Run the test case 1, the result is as expected.

2. Reset VF1 by setting mac addr::

    ip link set ens785f0 vf 1 mac 00:11:22:33:44:66

   Then execute below command in testpmd::

    port stop 1
    port reset 1
    port start 1
    start

3. Send same streams in step1 but with VF1's new mac address "00:11:22:33:44:66",
   check TC0 stream maps to all queues, TC1 and TC2 stream map to queue0.

4. Set the qos settings as test case 1 step2 again.
   send the same steams, check the same result as step 1.

Test case 15: link status change
================================
This case is to check if the QoS setting works after link status change.

1. Run the test case 1, the result is as expected.

2. Change the link status::

    ifconfig ens785f0 down

   Check TC setting is not changed, the queue mapping is not changed,
   The Tx rate is not changed.

3. Change the link status again::

    ifconfig ens785f0 up

   Check the status, get the same result.

Test case 16: DCB setting TC change
===================================
This case is to check if the QoS setting works after DCB setting TC change.

1. Run the test case 1, the result is as expected.

2. Reset the DCB setting as below::

    ./dcbgetset ens785f0  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,40,50,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0

3. Send the same streams as step 1,
   Only send TC0 stream, queue0-queue7 of both Rx and Tx have traffic, load is balancing.
   Only send TC1/TC2 streams, only queue0 has Rx and Tx traffic.

NOTE: The kernel default status is TC0 stream mapping to all queues, other TC streams mapping to queue 0.

Test case 17: negative case for requested VF
============================================
1. DCB setting, set 2 TCs bandwidth with strict mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,0,0,1,0,0,0,0 --tcbw 20,80,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0

2. Create 2 VFs::

    echo 2 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1
    ip link set dev ens785f0 vf 0 trust on
    ip link set ens785f0 vf 1 mac 00:11:22:33:44:55

3. Start testpmd with 100G setting::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -- -i --txq=8 --rxq=8 --port-topology=loop --nb-cores=8
    port stop all

Subcase 1: Requested VF id is valid
-----------------------------------
Set 3 VSIs, more than 2 VFs created::

    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0    
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0    
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0     
    node id: too many VSI for one TC (error 33)   

Subcase 2: Valid number of TCs for the target VF
------------------------------------------------
1. Configured 2 TCs by DCB, but only set 1 TC node::

    add port tm node shaper profile 0 1 63000 0 12500000000 0 0 0        
    add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0
    port tm hierarchy commit 0 yes
    ice_dcf_commit_check(): Not all enabled TC nodes are set
    no error: (no stated reason) (error 0)

2. Not all VFs are binded to TC node::

    add port tm node shaper profile 0 1 63000 0 12500000000 0 0 0
    add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800000 0 1 2 2 0 0xffffffff 0 0
    port tm hierarchy commit 0 yes
    ice_dcf_commit_check(): Not all VFs are binded to TC1
    no error: (no stated reason) (error 0)

3. Add 1 profile, but use 2 profiles::

    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0    
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0       
    shaper profile id field (node params): shaper profile not exist (error 23)

Subcase 3: Valid Min and Max values
-----------------------------------
1. Min default value is 500Kbps::

    add port tm node shaper profile 0 1 62999 0 2000000 0 0 0      
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0
    add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800000 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 3 800000 0 1 2 2 0 0xffffffff 0 0
    testpmd> port tm hierarchy commit 0 yes
    ice_dcf_execute_virtchnl_cmd(): No response (1 times) or return failure (-5) for cmd 37
    ice_dcf_set_vf_bw(): fail to execute command VIRTCHNL_OP_DCF_CONFIG_BW
    no error: (no stated reason) (error 0)

    add port tm node shaper profile 0 1 63000 0 2000000 0 0 0
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0
    add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800000 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 3 800000 0 1 2 2 0 0xffffffff 0 0
    testpmd> port tm hierarchy commit 0 no

   The setting commit successfully.

2.Min BW for the given TC must be less than that of Max BW::

    add port tm node shaper profile 0 1 2001000 0 2000000 0 0 0
    add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 3 800000 0 1 2 1 0 0xffffffff 0 0
    port tm hierarchy commit 0 yes
    ice_dcf_execute_virtchnl_cmd(): No response (1 times) or return failure (-5) for cmd 37
    ice_dcf_set_vf_bw(): fail to execute command VIRTCHNL_OP_DCF_CONFIG_BW
    no error: (no stated reason) (error 0)

    add port tm node shaper profile 0 1 2000000 0 2000000 0 0 0
    add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 3 800000 0 1 2 1 0 0xffffffff 0 0
    port tm hierarchy commit 0 yes

   The setting commit successfully.

3. Max BW must be less than or equal to negotiated link speed for the port
1).One iavf VF, two TCs::

    add port tm node shaper profile 0 1 1000000000 0 12000000000 0 0 0
    add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 3 800000 0 1 2 1 0 0xffffffff 0 0

    port tm hierarchy commit 0 yes
    ice_dcf_validate_tc_bw(): Total value of TC0 min bandwidth and other TCs' max bandwidth 104000000kbps should be less than port link speed 100000000kbps

2).Two iavf VF, two TCs::

    echo 3 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1 18:01.2
    ip link set dev ens785f0 vf 0 trust on
    ip link set ens785f0 vf 1 mac 00:11:22:33:44:55
    ip link set ens785f0 vf 2 mac 00:11:22:33:44:66
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -a 18:01.2 -a 18:01.3 -- -i --txq=8 --rxq=8 --port-topology=loop --nb-cores=8
    port stop all
    add port tm node shaper profile 0 1 10000000 0 1000000000 0 0 0
    add port tm node shaper profile 0 2 10000000 0 8500000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 4 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 5 800 0 1 2 2 0 0xffffffff 0 0
    port tm hierarchy commit 0 yes
    ice_dcf_validate_tc_bw(): Total value of TC0 min bandwidth and other TCs' max bandwidth 136160000kbps should be less than port link speed 100000000kbps
    no error: (no stated reason) (error 0)

4. Max BW cannot be 0 and must be greater than or equal to Min BW
   If set max BW to 0, there is not max rate limit::

    add port tm node shaper profile 0 1 0 0 0 0 0 0    
    add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800000 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 3 800000 0 1 2 1 0 0xffffffff 0 0
    port tm hierarchy commit 0 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    port start all
    set fwd mac
    start

   Send two streams from IXIA, vlan=0, priority=0/3(TC0/TC1),
   mac address is VF1's mac address "00:11:22:33:44:55", frame size is 1024 bytes, 100% max rate.
   send each stream separately, check the TX throughput of each TC can reach linerate.
   and the queue mapping is correct.

Test case 18: negative case for req VF to update its queue to TC mapping
========================================================================
1. DCB setting, set 3 TCs bandwidth with strict mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0

2. Create 2 VFs::

    echo 2 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    ./usertools/dpdk-devbind.py -b vfio-pci 18:01.0 18:01.1
    ip link set dev ens785f0 vf 0 trust on
    ip link set ens785f0 vf 1 mac 00:11:22:33:44:55

3. Start testpmd with 100G setting::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -- -i --txq=8 --rxq=8 --port-topology=loop --nb-cores=8
    port stop all

Subcase 1: Total number of queue pairs match to what the VF is allocated
------------------------------------------------------------------------
1. 8 queues, only map 7 queues to TC::

    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0
    port tm hierarchy commit 0 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    iavf_hierarchy_commit(): queue node is less than allocated queue pairs
    no error: (no stated reason) (error 0)

2. 8 queues, map 9 queues to TC::

    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 8 700 0 1 2 0 0 0xffffffff 0 0
    num strict priorities field (node params): SP priority not supported (error 27)

Subcase 1: Number of TCs match is less than TC enabled on the VF
----------------------------------------------------------------
1. Not all VF0 VSI nodes binded to TC::

    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0
    port tm hierarchy commit 0 yes
    ice_dcf_commit_check(): Not all VFs are binded to TC2
    no error: (no stated reason) (error 0)

2. Not all VF1 VSI nodes binded to TC::

    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0
    port tm hierarchy commit 0 no
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    iavf_hierarchy_commit(): Does not set VF vsi nodes to all TCs
    no error: (no stated reason) (error 0)

3. Not all VF1 VSI nodes mapping to queues, set successfully::

    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes

   Send TC0 and TC1 streams, the queue mapping is correct.

Subcase 3: Number of TCs match is more than TC enabled on the VF
----------------------------------------------------------------
The TC number should be consistent to the TC enabled by lldptool.
Run the below steps sequentially.

1. TC node number is more than TC enabled by lldptool::

    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0    
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0   
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0  
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0     
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0  
    add port tm nonleaf node 0 600 1000 0 1 1 -1 1 0 0  
    node id: too many TCs (error 33)

2. VF0's TC node number is more than TC enabled by lldptool::

    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0       
    add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0       
    add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0          
    add port tm leaf node 0 6 600 0 1 2 2 0 0xffffffff 0 0       
    parent node id: parent not exist (error 19)

3. VF1's TC node number is more than TC enabled by lldptool::

    port tm hierarchy commit 0 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 600 1000 0 1 1 0 1 0 0
    node id: too many TCs (error 33)

4. Map the nonexist VSI node to queues::

    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 600 0 1 2 0 0 0xffffffff 0 0
    parent node id: parent not exist (error 19)

Subcase 4: overlap between queue to TC mapping
----------------------------------------------
There can't be overlap between queue to TC mapping::

    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0
    port tm hierarchy commit 0 no
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 800 0 1 2 0 0 0xffffffff 0 0
    node id: node id already used (error 33)

Subcase 5: Non-contiguous TC setting in queue mapping
-----------------------------------------------------
1. Set non-contiguous TC and queue mapping::

    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0    
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0    
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0    
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0     
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0  
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0        
    add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0       
    add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0       
    add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0          
    port tm hierarchy commit 0 yes
    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 yes
    port start all
    set fwd mac
    start

2. Send four streams from IXIA, vlan=0, priority=2/5/3/4(TC0/TC0/TC1/TC2),
   mac address is VF1's mac address "00:11:22:33:44:55".
   frame size is 68 bytes, each stream desired 25% max rate.
   send each stream separately, check the TX throughput of each priority and queue mapping:
   UP=2/5 which matches to TC0, maps to queue0-1, throughput can reach 2MBps,
   UP=3 which matches to TC1, maps to queue2-3, throughput can reach 4MBps,
   UP=4 which matches to TC2, maps to queue4-7. throughput can reach 4MBps.

Test case 19: different vlan ID
===============================
There are different streams with different vlan id, but with same user priority.
The sum of the streams's throughput is limited by the tcbw distribution or peak_tb_rate.

1. DCB setting, set 3 TCs bandwidth with strict mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0
    ifconfig ens785f0 up

2. Start testpmd with 100G setting, add vlan filter,
   Then set profile and TC mapping::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-10 -n 4 -a 18:01.0,cap=dcf -a 18:01.1 -- -i --txq=8 --rxq=8 --nb-cores=8 --port-topology=loop
    port stop all
    vlan set filter on 1
    rx_vlan add 1 1
    rx_vlan add 2 1

    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0

    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0
    port tm hierarchy commit 0 no

    add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0
    add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0
    add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0
    add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0
    add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0
    port tm hierarchy commit 1 no
    port start all
    set fwd mac
    start

3. Send 8 streams from IXIA, mac address is VF1's mac address "00:11:22:33:44:55",
   frame size is 68 bytes, each stream desired 25% max rate.
   stream 0-3, vlan id=0, priority=0/1/3/4(TC0/TC0/TC1/TC2),
   stream 4-5, vlan id=1, priority=0/3(TC0/TC1),
   stream 6-7, vlan id=2, priority=2/4(TC0/TC2).
   only send stream 0,1,4,6 synchronously, the throughput is 2MBps, mapping queue 0-3
   only send steam 2 and 5 synchronously, the throughput is 4MBps, mapping queue 4-5
   only send steam 3 and 7 synchronously, the throughput is 4MBps, mapping queue 6-7
   send all the streams synchronously, the throughput is 10MBps, queue mapping is correct,
   which is same as previous steps.

Test case 20: delete qos setting
================================
The case is to check the support to delete QoS settings.

1. DCB setting, set 3 TCs bandwidth with strict mode::

    ./dcbgetset ens785f0  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0
    ifconfig ens785f0 up

2. Start testpmd with 100G setting, then set profile and TC mapping::

    port stop all
    add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0
    add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0
    add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0
    add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0
    add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0
    add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0
    add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0
    add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0

3. Delete the shaper profile and nonleaf node::

    del port tm node 0 1000
    node id: cannot delete a node which has children (error 33)
    del port tm node 0 700
    node id: cannot delete a node which has children (error 33)
    del port tm node shaper profile 0 1
    shaper profile null: profile in use (error 10)

   The nodes can't be deleted due to the children nodes.
   Delete the leaf nodes first, then delete the nonleaf nodes and shaper profile::

    del port tm node 0 5
    del port tm node 0 4
    del port tm node 0 3
    del port tm node 0 2
    del port tm node 0 1
    del port tm node 0 0
    del port tm node 0 700
    del port tm node 0 800
    del port tm node 0 900
    del port tm node 0 1000
    del port tm node shaper profile 0 1
    del port tm node shaper profile 0 2

   Deleted successfully.

4. Add the settings again as step2, then commit the configuration::

    port tm hierarchy commit 0 no

   Delete the leaf node::

    del port tm node 0 5
    cause unspecified: already committed (error 1)

   Check the node can't be deleted after committed.

5. All the operation has the same result on port 1.
