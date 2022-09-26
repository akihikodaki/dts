.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2015-2017 Intel Corporation

==============================================
VF Request Queue Number From Kernel At Runtime
==============================================

Both kernel driver, I40E and DPDK PMD driver, igb_uio/vfio-pci support
VF request queue number at runtime, that means the users could configure
the VF queue number at runtime.

This feature support 2 scenarios:

#. DPDK VF + DPDK PF: see runtime_vf_queue_number_test_plan.rst
#. DPDK VF + Kernel PF: see runtime_vf_queue_number_kernel_test_plan.rst(current file)

Prerequisites
=============

1. Hardware:

- Intel® Ethernet 700 Series(X710/XL710/XXV710)
- Intel® Ethernet 800 Series

2. Software:

- DPDK: http://dpdk.org/git/dpdk (version: 19.02+)
- Scapy: http://www.secdev.org/projects/scapy/

3. Scenario:

- Kernel PF + DPDK VF

4. test topology:

.. figure:: image/2vf1pf.png

Set up scenario
===============

Assume create 2 vf from 1 pf.

1. Make sure PF is binded to kernel driver, i40e::

     usertools/dpdk-devbind.py --s
     0000:87:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=

2. Create 2 VF from PF::

     echo 2 > /sys/bus/pci/devices/0000\:87\:00.0/sriov_numvfs

     usertools/dpdk-devbind.py --s
     0000:87:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
     0000:87:02.0 'XL710/X710 Virtual Function' unused=
     0000:87:02.1 'XL710/X710 Virtual Function' unused=

3. Detach VF from the host, bind them to DPDK drvier, here take vfio-pci for example::

     modprobe vfio
     modprobe vfio-pci

Note: there are 2 ways to bind devices to vfio-pci:

- Leverage usertools in dpdk package::

     usertools/dpdk-devbind.py --bind=vfio-pci 0000:18:02.0
     usertools/dpdk-devbind.py --bind=vfio-pci 0000:18:02.1

- Leverage Linux command::

     using `lspci -nn|grep -i ethernet` got VF device id, for example "8086 154c",

     echo "8086 154c" > /sys/bus/pci/drivers/vfio-pci/new_id
     echo 0000:18:02.0 > /sys/bus/pci/devices/0000:18:02.0/driver/unbind
     echo 0000:18:02.0 > /sys/bus/pci/drivers/vfio-pci/bind

     echo "8086 154c" > /sys/bus/pci/drivers/vfio-pci/new_id
     echo 0000:18:02.1 > /sys/bus/pci/devices/0000:18:02.1/driver/unbind
     echo 0000:18:02.1 > /sys/bus/pci/drivers/vfio-pci/bind

4. Passthrough VFs 18:02.0 to vm0 and start vm0::

     /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
     -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-1.img -vnc :1 \
     -device vfio-pci,host=0000:18:02.0,id=pt_0 \
     -device vfio-pci,host=0000:18:02.1,id=pt_0 \

Now the scenario has been set up, you will have 2 vfs passthoughed to VM.


5. Login vm0 and them bind VF devices to igb_uio driver::

    ./usertools/dpdk-devbind.py --bind=igb_uio 00:04.0
    ./usertools/dpdk-devbind.py --bind=igb_uio 00:05.0

Test Case 1: set valid VF queue number in testpmd command-line options
======================================================================

1. Start VF testpmd with "--rxq=[rxq] --txq=[txq]", and random valid values from 1 to 16, take 3 for example::

     ./<build_target>/app/dpdk-testpmd -c 0xf0 -n 4 -a 00:04.0 --file-prefix=test2 \
     --socket-mem 1024,1024 -- -i --rxq=3 --txq=3

2. Configure vf forwarding prerequisits and start forwarding::

     testpmd> set promisc all off
     testpmd> set fwd mac

3. Start forwarding, and verfiy the queue number informantion. Both the RX queue number and the TX queue number must be same as your configuration. Here is 3::

     testpmd> start

     port 0: RX queue number: 3 Tx queue number: 3

4. Send packets to VF from tester, and make sure they match the default RSS rules, IPV4_UNKNOW, and will be distributed to all the queues that you configured, Here is 3::

     pkt1 = Ether(dst="$vf_mac", src="$tester_mac")/IP(src="10.0.0.1",dst="192.168.0.1")/("X"*48)
     pkt2 = Ether(dst="$vf_mac", src="$tester_mac")/IP(src="10.0.0.1",dst="192.168.0.2")/("X"*48)
     pkt3 = Ether(dst="$vf_mac", src="$tester_mac")/IP(src="10.0.0.1",dst="192.168.0.3")/("X"*48)

5. Stop forwarding, and check the queues statistics, every RX/TX queue must has 1 packet go through, and total 3 packets in uni-direction as well as 6 packets in bi-direction::

    testpmd> stop

      ------- Forward Stats for RX Port= 0/Queue= 0 -> TX Port= 0/Queue= 0 -------
      RX-packets: 1       TX-packets: 1       TX-dropped: 0
      ------- Forward Stats for RX Port= 0/Queue= 1 -> TX Port= 0/Queue= 1 -------
      RX-packets: 1              TX-packets: 1             TX-dropped: 0
      ------- Forward Stats for RX Port= 0/Queue= 2 -> TX Port= 0/Queue= 2 -------
      RX-packets: 1              TX-packets: 1             TX-dropped: 0
      ---------------------- Forward statistics for port 0  ----------------------
      RX-packets: 3      RX-dropped: 0     RX-total: 3
      TX-packets: 3       TX-dropped: 0             TX-total: 3
      ----------------------------------------------------------------------------

6. Repeat step 1 to 5 with the mininum queue number, 1, and the maximum queue number, 16.

Test case 2: set invalid VF queue number in testpmd command-line options
========================================================================

1. Start VF testpmd with "--rxq=0 --txq=0" ::

     ./<build_target>/app/dpdk-testpmd -c 0xf0 -n 4 -a 00:04.0 --file-prefix=test2 \
     --socket-mem 1024,1024 -- -i --rxq=0 --txq=0

   Verify testpmd exited with error as below::

    Either rx or tx queues should be non-zero

2. Start VF testpmd with "--rxq=17 --txq=17" ::

    ./<build_target>/app/dpdk-testpmd -c 0xf0 -n 4 -a 00:04.0 --file-prefix=test2 \
    --socket-mem 1024,1024 -- -i --rxq=17 --txq=17

   Verify testpmd exited with error as below::

    txq 17 invalid - must be >= 0 && <= 16

Test case 3: set valid VF queue number with testpmd function command
====================================================================

1. Start VF testpmd without setting "rxq" and "txq"::

    ./<build_target>/app/dpdk-testpmd -c 0xf0 -n 4 -a 00:04.0 --socket-mem 1024,1024 -- -i

2. Configure vf forwarding prerequisits and start forwarding::

    testpmd> set promisc all off
    testpmd> set fwd mac

3. Set rx queue number and tx queue number with random value range from 1 to 16 with testpmd function command, take 3 for example::

    testpmd> port stop all
    testpmd> port config all rxq 3
    testpmd> port config all txq 3
    testpmd> port start all

4. Repeat step 3-6 of test case 1.

Test case 4: set invalid VF queue number with testpmd function command
======================================================================

1. Start VF testpmd without setting "rxq" and "txq"::

     ./<build_target>/app/dpdk-testpmd -c 0xf0 -n 4 -a 00:04.0 --socket-mem 1024,1024 -- -i

2. Set rx queue number and tx queue number with 0 ::

     testpmd> port stop all
     testpmd> port config all rxq 0
     testpmd> port config all txq 0
     testpmd> port start all

3. Set rx queue number and tx queue number with 17 ::

     testpmd> port stop all
     testpmd> port config all rxq 17
     testpmd> port config all txq 17
     testpmd> port start all

   Verify error information::

     Fail: input rxq (17) can't be greater than max_rx_queues (16) of port 0
