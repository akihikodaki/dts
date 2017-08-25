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

===========================
VFD as SRIOV Policy Manager
===========================

VFD is SRIOV Policy Manager (daemon) running on the host allowing
configuration not supported by kernel NIC driver, supports ixgbe and
i40e NIC. Run on the host for policy decisions w.r.t. what a VF can and
cannot do to the PF. Only the DPDK PF would provide a callback to implement 
these features, the normal kernel drivers would not have the callback so 
would not support the features. Allow passing information to application 
controlling PF when VF message box event received such as those listed below, 
so action could be taken based on host policy. Stop VM1 from asking for 
something that compromises VM2. Use DPDK DPDK PF + kernel VF mode to verify 
below features. 

Test Case 1: Set up environment and load driver
===============================================
1. Get the pci device id of DUT, load ixgbe driver to required version, 
   take Niantic for example::

    rmmod ixgbe
    insmod ixgbe.ko

2. Host PF in DPDK driver. Create VFs from PF with dpdk driver::

	./tools/dpdk-devbind.py -b igb_uio 05:00.0
	echo 2 >/sys/bus/pci/devices/0000\:05\:00.0/max_vfs 
	
3. Check ixgbevf version and update ixgbevf to required version
	
4. Detach VFs from the host::

    rmmod ixgbevf

5. Pass through VF 05:10.0 and 05:10.2 to VM0,start and login VM0

6. Check ixgbevf version in VM and update to required version


Test Case 2: Link
=================
Pre-environment::

  (1)Host one DPDK PF and create two VFs, pass through VF0 and VF1 to VM0,
     start VM0 
  (2)Load host DPDK driver and VM0 kernel driver

Steps:  

1. Enable multi-queues to start DPDK PF::

    ./testpmd -c f -n 4 -- -i --rxq=4 --txq=4

2. Link up kernel VF and expect VF link up

3. Link down kernel VF and expect VF link down

4. Repeat above 2~3 for 100 times, expect no crash or core dump issues. 


Test Case 3: ping 
==================
Pre-environment:: 

  (1)Establish link with link partner.
  (2)Host one DPDK PF and create two VFs, pass through VF0 and VF1 to VM0,
     start VM0
  (3)Load host DPDK driver and VM0 kernel driver

Steps: 

1. Ifconfig IP on VF0 and VF1

2. Ifconfig IP on link partner PF, name as tester PF

3. Start inbound and outbound pings, check ping successfully.

4. Link down the devx, stop the pings, link up the devx then restart the 
   pings, check port could ping successfully. 

5. Repeat step 3~4 for 5 times
   

Test Case 4: reset
==================
Pre-environment::

  (1)Establish link with link partner.
  (2)Host one DPDK PF and create two VFs, pass through VF0 to VM0 and VF1 to
     VM1, start VM0 and VM1
  (3)Load host DPDK driver and VM kernel driver

Steps: 

1. Check host testpmd and PF at link up status

2. Link up VF0 in VM0 and VF1 in VM1 

3. Link down VF1 in VM1 and check no impact on VF0 status

4. Unload VF1 kernel driver and expect no impact on VF0 

5. Use tcpdump to dump packet on VF0

6. Send packets to VF0 using IXIA or scapy tool, expect RX successfully

7. Link down and up DPDK PF, ensure that the VF recovers and continues to 
   receive packet. 

8. Load VF1 kernel driver and expect no impact on VF0

9. Send packets to VF0 using IXIA or scapy tool, expect RX successfully


Test Case 5: add/delete IP/MAC address
==========================================
Pre-environment::

    (1)Establish link with link partner.
    (2)Host one DPDK PF and create one VF, pass through VF0 to VM0, start VM0
    (3)Load host DPDK driver and VM0 kernel drive

Steps: 

1. Ifconfig IP on kernel VF0 

2. Ifconfig IP on link partner PF, name as tester PF

3. Kernel VF0 ping tester PF, tester PF ping kernel VF0

4. Add IPv6 on kernel VF0(e.g: ens3)::

    ifconfig ens3 add efdd::9fc8:6a6d:c232:f1c0

5. Delete IPv6 on kernel VF::

    ifconfig ens3 del efdd::9fc8:6a6d:c232:f1c0

6. Modify MAC address on kernel VF::

    ifconfig ens3 hw ether 00:AA:BB:CC:dd:EE

7. Send packet to modified MAC, expect VF can receive packet successfully


Test Case 6: add/delete vlan
==========================================
Pre-environment::

    (1)Establish link with link partner.
    (2)Host one DPDK PF and create one VF, pass through VF0 to VM0, start VM0
    (3)Load host DPDK driver and VM0 kernel driver

Steps: 

1. Add random vlan id(0~4095) on kernel VF0(e.g: ens3), take vlan id 51 
   for example::

    modprobe 8021q
    vconfig add ens3 51

2. Check add vlan id successfully, expect to have ens3.51 device::

    ls /proc/net/vlan

3. Send packet from tester to VF MAC with not-matching vlan id, check the 
   packet can't be received at the vlan device

4. Send packet from tester to VF MAC with matching vlan id, check the 
   packet can be received at the vlan device.

5. Delete configured vlan device::

    vconfig rem ens3.51

6. Check delete vlan id 51 successfully

7. Send packet from tester to VF MAC with vlan id(51), check that the 
   packet can’t be received at the VF. 


Test Case 7: Get packet statistic
==========================================
Pre-environment::

    (1)Establish link with link partner.
    (2)Host one DPDK PF and create one VF, pass through VF0 to VM0, start VM0
    (3)Load host DPDK driver and VM0 kernel driver

Steps: 

1. Send packet to kernel VF0 mac

2. Check packet statistic could increase correctly::

    ethtool -S ens3


Test Case 8: MTU
==========================================
Pre-environment::

    (1)Establish link with link partner.
    (2)Host one DPDK PF and create one VF, pass through VF0 to VM0, start VM0
    (3)Load host DPDK driver and VM0 kernel driver

Steps: 

1. Check DPDK PF and kernel VF mtu, normal as 1500

2. Use scapy to send one packet with length as 2000 with DPDK PF MAC as 
   DST MAC, check that DPDK PF can't receive packet

3. Use scapy to send one packet with length as 2000 with kernel VF MAC as 
   DST MAC, check that Kernel VF can't receive packet

4. Change DPDK PF mtu as 3000,check no confusion/crash on kernel VF::

    Testpmd > port stop all
    Testpmd > port config mtu 0 3000
    Testpmd > port start all

5. Use scapy to send one packet with length as 2000 with DPDK PF MAC as 
   DST MAC, check that DPDK PF can receive packet

6. Change kernel VF mtu as 3000, check no confusion/crash on DPDK PF::

    ifconfig eth0 mtu 3000

7. Use scapy to send one packet with length as 2000 with kernel VF MAC 
   as DST MAC, check Kernel VF can receive packet

Note:
HW limitation on 82599, need add “--max-pkt-len=<length>” on testpmd to 
set mtu value, all the VFs and PF share same MTU, the largest one takes 
effect.


Test Case 9: Enable/disable promisc mode
=========================================
Pre-environment::

    (1)Establish link with link partner.
    (2)Host one DPDK PF and create one VF, pass through VF0 to VM0, start VM0
    (3)Load host DPDK driver and VM0 kernel driver

Steps:
 
1. Start DPDK PF, enable promisc mode, set rxonly forwarding

2. Set up kernel VF tcpdump without -p parameter, without/with -p parameter 
   could enable/disable promisc mode::

    sudo tcpdump -i ens3 -n -e -vv

3. Send packet from tester with random DST MAC, check the packet can be 
   received by DPDK PF and kernel VF

4. Disable DPDK PF promisc mode

5. Set up kernel VF tcpdump with -p parameter, which means disable promisc 
   mode::

    sudo tcpdump -i ens3 -n -e –vv -p

6. Send packet from tester with random DST MAC, check the packet can't be 
   received by DPDK PF and kernel VF

7. Send packet from tester to VF with correct DST MAC, check the packet 
   can be received by kernel VF

8. Send packet from tester to PF with correct DST MAC, check the packet 
   can be received by DPDK PF

Note: 
Niantic NIC un-supports this case.


Test Case 10: RSS
=========================================
Pre-environment::

    (1)Establish link with link partner.
    (2)Host one DPDK PF and create one VF, pass through VF0 to VM0, start VM0
    (3)Load host DPDK driver and VM0 kernel driver

Steps: 

1. Verify kernel VF RSS using ethtool -"l" (lower case L) <devx> that the 
   default RSS setting is equal to the number of CPUs in the system and 
   that the maximum number of RSS queues displayed is correct for the DUT

2. Run "ethtool -S <devx> | grep rx_bytes | column" to see the current 
   queue count and verify that it is correct to step 1

3. Send multi-threaded traffics to the DUT with a number of threads  

4. Check kernel VF each queue can receive packets

Note: 
Niantic NIC un-supports this case.


Test Case 11: DPDK PF + kernel VF + DPDK VF
============================================
Pre-environment::

    (1)Establish link with IXIA.
    (2)Host one DPDK PF and create two VFs, pass through VF0 and VF1 to VM0,
       start VM0
    (3)Load host DPDK driver, VM0 DPDK driver and kernel driver 

Steps:
 
1. Check DPDK testpmd and PF at link up status

2. Bind kernel VF0 to igb_uio

3. Link up DPDK VF0

4. Link up kernel VF1

5. Start DPDK VF0, enable promisc mode and set rxonly forwarding

6. Set up kernel VF1 tcpdump without -p parameter on promisc mode

7. Create 2 streams on IXIA, set DST MAC as each VF MAC, transmit these 2 
   streams at the same time, check DPDK VF0 and kernel VF1 can receive packet 
   successfully 

8. Check DPDK VF0 and kernel VF1 don't impact each other and no performance 
   drop for 10 minutes


Test Case 12: DPDK PF + 2kernel VFs + 2DPDK VFs + 2VMs
======================================================
Pre-environment::

    (1)Establish link with IXIA.
    (2)Host one DPDK PF and create 6 VFs, pass through VF0, VF1, VF2 and VF3
       to VM0, pass through VF4, VF5 to VM1, start VM0 and VM1
    (3)Load host DPDK driver, VM DPDK driver and kernel driver

Steps:
 
1. Check DPDK testpmd and PF at link up status

2. Bind kernel VF0, VF1 to igb_uio in VM0, bind kernel VF4 to igb_uio in VM1

3. Link up DPDK VF0,VF1 in VM0, link up DPDK VF4 in VM1

4. Link up kernel VF2, VF3 in VM0, link up kernel VF5 in VM1

5. Start DPDK VF0, VF1 in VM0 and VF4 in VM1, enable promisc mode and set 
   rxonly forwarding

6. Set up kernel VF2, VF3 in VM0 and VF5 in VM1 tcpdump without -p parameter 
   on promisc mode

7. Create 6 streams on IXIA, set DST MAC as each VF MAC, transmit 6 streams 
   at the same time, expect RX successfully

8. Link down DPDK VF0 and expect no impact on other VFs

9. Link down kernel VF2 and expect no impact on other VFs

10. Quit VF4 DPDK testpmd and expect no impact on other VFs

11. Unload VF5 kernel driver and expect no impact on other VFs

12. Reboot VM1 and expect no impact on VM0’s VFs 


Test Case 13: Load kernel driver stress
========================================
Pre-environment::

    (1)Host one DPDK PF and create one VF, pass through VF0 to VM0, start VM0
    (2)Load host DPDK driver and VM0 kernel driver

Steps:
 
1. Check DPDK testpmd and PF at link up status

2. Unload kernel VF0 driver

3. Load kernel VF0 driver

4. Write script to repeat step 2 and step 3 for 100 times stress test

4. Check no error/crash and system work normally
  
