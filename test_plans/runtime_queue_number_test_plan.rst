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

=====================================
Dynamically Configure VF Queue Number
=====================================

Description
===========

   Now RTE_LIBRTE_I40E_QUEUE_NUM_PER_VF is used to determine the max queue
   number per VF. It's not friendly to the users because it means the users
   must decide the max queue number when compiling. There's no chance to
   change it when deploying their APP. It's good to make the queue number
   to be configurable so the users can change it when launching the APP.
   This requirement is meaningless to ixgbe since the queue is fixed on
   ixgbe.
   The number of queues per i40e VF can be determinated
   during run time. For example, if the PCI address of an i40e PF is
   aaaa:bb.cc, with the EAL parameter -w aaaa:bb.cc,queue-num-per-vf=8,
   the number of queues per VF created from this PF is 8.
   Set the VF max queue number with the PF EAL parameter "queue-num-per-vf".
   the valid values includes 1,2,4,8,16; if the value after the
   "queue-num-per-vf" is invalid, it is set as 4 forcibly;
   if there is no "queue-num-per-vf" setting in EAL parameters,
   it is 4 by default as before.

Prerequisites
=============

1. Hardware:
   Fortville

2. Software:
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Bind the pf port to dpdk driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0

4. Set up two vfs from the pf with DPDK driver::

    echo 2 > /sys/bus/pci/devices/0000\:05\:00.0/max_vfs

   Bind the two vfs to DPDK driver::

    ./usertools/dpdk-devbind.py -b vfio-pci 05:02.0 05:02.1

Test case: set valid VF max queue number 
========================================

1. Try the valid values 1::

    ./testpmd -c f -n 4 -w 05:00.0,queue-num-per-vf=1 \
    --file-prefix=test1 --socket-mem 1024,1024 -- -i
  
   Testpmd can be started normally without any wrong or error.

2. Start VF testpmd with "--rxq=1 --txq=1", the number of rxq and txq is
   consistent with the configured VF max queue number::

    ./testpmd -c 0xf0 -n 4 -w 05:02.0 \
    --file-prefix=test2 --socket-mem 1024,1024 -- -i --rxq=1 --txq=1

   Check the Max possible RX queues and TX queues is 1::

    testpmd> show port info all
    Max possible RX queues: 1
    Max possible number of RXDs per queue: 4096
    Min possible number of RXDs per queue: 64
    RXDs number alignment: 32
    Max possible TX queues: 1
    Max possible number of TXDs per queue: 4096
    Min possible number of TXDs per queue: 64
    TXDs number alignment: 32
 
   Start forwarding, you can see the actual queue number is 1::

    testpmd> start
    RX queues=1 - RX desc=128 - RX free threshold=32
    TX queues=1 - TX desc=512 - TX free threshold=32 

3. Repeat step1-2 with "queue-num-per-vf=2/4/8/16", and start VF testpmd
   with consistent rxq and txq number. check the max queue num and actual
   queue number is 2/4/8/16.

Test case: set invalid VF max queue number
==========================================

1. Try the invalid value 0::

    ./testpmd -c f -n 4 -w 05:00.0,queue-num-per-vf=0 \
    --file-prefix=test1 --socket-mem 1024,1024 -- -i

   Testpmd started with "i40e_pf_parse_vf_queue_number_handler(): Wrong
   VF queue number = 0, it must be power of 2 and equal or less than 16 !,
   Now it is kept the value = 4"

2. Start VF testpmd with "--rxq=4 --txq=4", the number of rxq and txq is
   consistent with the default VF max queue number::

    ./testpmd -c 0xf0 -n 4 -w 05:02.0 --file-prefix=test2 \
    --socket-mem 1024,1024 -- -i --rxq=4 --txq=4

   Check the Max possible RX queues and TX queues is 4::

    testpmd> show port info all
    Max possible RX queues: 4
    Max possible TX queues: 4

   Start forwarding, you can see the actual queue number is 4::

    testpmd> start
    RX queues=4 - RX desc=128 - RX free threshold=32
    TX queues=4 - TX desc=512 - TX free threshold=32

3. Repeat step1-2 with "queue-num-per-vf=6/17/32", and start VF testpmd
   with default max rxq and txq number. check the max queue num and actual
   queue number is 4.

Test case: set VF queue number in testpmd command-line options
==============================================================

1. Set VF max queue number::

    ./testpmd -c f -n 4 -w 05:00.0,queue-num-per-vf=8 \
    --file-prefix=test1 --socket-mem 1024,1024 -- -i

2. Start VF testpmd with "--rxq=3 --txq=3"::

    ./testpmd -c 0xf0 -n 4 -w 05:02.0 --file-prefix=test2 \
    --socket-mem 1024,1024 -- -i --rxq=3 --txq=3

   Check the Max possible RX queues and TX queues is 8::

    testpmd> show port info all
    Max possible RX queues: 8
    Max possible TX queues: 8

   Start forwarding, you can see the actual queue number is 3::

    testpmd> start
    RX queues=3 - RX desc=128 - RX free threshold=32
    TX queues=3 - TX desc=512 - TX free threshold=32

3. Quit the VF testpmd, then restart VF testpmd with "--rxq=9 --txq=9"::

    ./testpmd -c 0xf0 -n 4 -w 05:02.0 --file-prefix=test2 \
    --socket-mem 1024,1024 -- -i --rxq=9 --txq=9

   VF testpmd failed to start with the print::

    Fail: nb_rxq(9) is greater than max_rx_queues(8)

Test case: set VF queue number with testpmd function command
============================================================

1. Set VF max queue number::

    ./testpmd -c f -n 4 -w 05:00.0,queue-num-per-vf=8 \
    --file-prefix=test1 --socket-mem 1024,1024 -- -i

2. Start VF testpmd without setting "rxq" and "txq"::

    ./testpmd -c 0xf0 -n 4 -w 05:02.0 --file-prefix=test2 \
    --socket-mem 1024,1024 -- -i

   Check the Max possible RX queues and TX queues is 8,
   and actual RX queue number and TX queue number is 1::

    testpmd> show port info all
    Current number of RX queues: 1
    Max possible RX queues: 8
    Current number of TX queues: 1
    Max possible TX queues: 8

3. Set rx queue number and tx queue number with testpmd function command::

    testpmd> port stop all
    testpmd> port config all rxq 8
    testpmd> port config all txq 8
    testpmd> port start all

4. Start forwarding, you can see the actual queue number is 8::

    testpmd> show port info all
    Current number of RX queues: 8
    Max possible RX queues: 8
    Current number of TX queues: 8
    Max possible TX queues: 8

5. Reset rx queue number and tx queue number to 7::

    testpmd> port stop all
    testpmd> port config all rxq 7
    testpmd> port config all txq 7
    testpmd> port start all

   Start forwarding, you can see the actual queue number is 7::

    testpmd> show port info all
    Current number of RX queues: 7
    Max possible RX queues: 8
    Current number of TX queues: 7
    Max possible TX queues: 8

6. Reset rx queue number and tx queue number to 9::

    testpmd> port stop all
    testpmd> port config all txq 9
    Fail: nb_txq(9) is greater than max_tx_queues(8)
    testpmd> port config all rxq 9
    Fail: nb_rxq(9) is greater than max_rx_queues(8)
    testpmd> port start all

   Start forwarding, you can see the actual queue number is still 7::

    testpmd> show port info all
    Current number of RX queues: 7
    Max possible RX queues: 8
    Current number of TX queues: 7
    Max possible TX queues: 8

Test case: VF max queue number when VF bound to kernel driver
=============================================================

1. Set VF max queue number by PF::

    ./testpmd -c f -n 4 -w 05:00.0,queue-num-per-vf=2 \
    --file-prefix=test1 --socket-mem 1024,1024 -- -i

2. Check the VF0 rxq and txq number is 2::

    # ethtool -S enp5s2
    NIC statistics:
         rx_bytes: 0
         rx_unicast: 0
         rx_multicast: 0
         rx_broadcast: 0
         rx_discards: 0
         rx_unknown_protocol: 0
         tx_bytes: 0
         tx_unicast: 0
         tx_multicast: 0
         tx_broadcast: 0
         tx_discards: 0
         tx_errors: 0
         tx-0.packets: 0
         tx-0.bytes: 0
         tx-1.packets: 0
         tx-1.bytes: 0
         rx-0.packets: 0
         rx-0.bytes: 0
         rx-1.packets: 0
         rx-1.bytes: 0

   Check the VF1 rxq and txq number is 2 too.
 
3. Repeat step1-2 with "queue-num-per-vf=1/4/8/16", check the rxq and txq
   number is 1/4/8/16.

Test case: set VF max queue number with 32 VFs on one PF port
=============================================================

1. Set up 32 VFs from one PF with DPDK driver::

    echo 32 > /sys/bus/pci/devices/0000\:05\:00.0/max_vfs

   Bind the two of the VFs to DPDK driver::

    ./usertools/dpdk-devbind.py -b vfio-pci 05:02.0 05:05.7 

2. Set VF max queue number to 16::

    ./testpmd -c f -n 4 -w 05:00.0,queue-num-per-vf=16 \
    --file-prefix=test1 --socket-mem 1024,1024 -- -i

   PF port failed to started with "i40e_pf_parameter_init():
   Failed to allocate 577 queues, which exceeds the hardware maximum 384"

3. Set VF max queue number to 8::

    ./testpmd -c f -n 4 -w 05:00.0,queue-num-per-vf=8 \
    --file-prefix=test1 --socket-mem 1024,1024 -- -i

4. Start the two VFs testpmd with "--rxq=8 --txq=8" and "--rxq=6 --txq=6"::

    ./testpmd -c 0xf0 -n 4 -w 05:02.0 --file-prefix=test2 \
    --socket-mem 1024,1024 -- -i --rxq=8 --txq=8

    ./testpmd -c 0xf00 -n 4 -w 05:05.7 --file-prefix=test3 \
    --socket-mem 1024,1024 -- -i --rxq=6 --txq=6

   Check the Max possible RX queues and TX queues of the two VFs are both 8::

    testpmd> show port info all
    Max possible RX queues: 8
    Max possible TX queues: 8

   Start forwarding, you can see the actual queue number
   VF0::

    testpmd> start
    RX queues=8 - RX desc=128 - RX free threshold=32
    TX queues=8 - TX desc=512 - TX free threshold=32

   VF1::

    testpmd> start
    RX queues=6 - RX desc=128 - RX free threshold=32
    TX queues=6 - TX desc=512 - TX free threshold=32

   Modify the queue number of VF1::

    testpmd> stop
    testpmd> port stop all
    testpmd> port config all rxq 8
    testpmd> port config all txq 7
    testpmd> port start all

   Start forwarding, you can see the VF1 actual queue number is 8 and 7::

    testpmd> start
    RX queues=8 - RX desc=128 - RX free threshold=32
    TX queues=7 - TX desc=512 - TX free threshold=32

Test case: pass through VF to VM
================================

1. Bind the pf to dpdk driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0

   Create 1 vf from pf::

    echo 1 >/sys/bus/pci/devices/0000:05:00.0/max_vfs

   Detach VF from the host, bind them to pci-stub driver::

    modprobe pci-stub
    echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
    echo "0000:05:02.0" > /sys/bus/pci/drivers/i40evf/unbind
    echo "0000:05:02.0" > /sys/bus/pci/drivers/pci-stub/bind

   Lauch the VM with the VF PCI passthrough::

    taskset -c 5-20 qemu-system-x86_64 \
    -enable-kvm -m 8192 -smp cores=16,sockets=1 -cpu host -name dpdk1-vm1 \
    -drive file=/home/VM/ubuntu-14.04.img \
    -device pci-assign,host=0000:05:02.0 \
    -netdev tap,id=ipvm1,ifname=tap3,script=/etc/qemu-ifup -device rtl8139,netdev=ipvm1,id=net0,mac=00:00:00:00:00:01 \
    -localtime -vnc :2 -daemonize

2. Set VF Max possible RX queues and TX queues to 8 by PF::

    ./testpmd -c f -n 4 -w 05:00.0,queue-num-per-vf=8 \
    --file-prefix=test1 --socket-mem 1024,1024 -- -i

   Testpmd can be started normally without any wrong or error.

3. Start VF testpmd with "--rxq=6 --txq=6", the number of rxq and txq is
   consistent with the configured VF max queue number::

    ./testpmd -c 0xf -n 4 -- -i --rxq=6 --txq=6

   Check the Max possible RX queues and TX queues is 8::

    testpmd> show port info all
    Max possible RX queues: 8
    Max possible TX queues: 8

   Start forwarding, you can see the actual queue number is 6::

    testpmd> start
    RX queues=6 - RX desc=128 - RX free threshold=32
    TX queues=6 - TX desc=512 - TX free threshold=32

   Modify the queue number of VF::

    testpmd> stop
    testpmd> port stop all
    testpmd> port config all rxq 8
    testpmd> port config all txq 8
    testpmd> port start all

   Start forwarding, you can see the VF1 actual queue number is 8::

    testpmd> start
    RX queues=8 - RX desc=128 - RX free threshold=32
    TX queues=8 - TX desc=512 - TX free threshold=32

4. Repeat step2-3 with "queue-num-per-vf=1/2/4/16", and start VF testpmd
   with consistent rxq and txq number. check the max queue num and actual
   queue number is 1/2/4/16.
 
5. Bind VF to kernel driver i40evf, check the rxq and txq number.
   if set VF Max possible RX queues and TX queues to 2 by PF,
   the VF rxq and txq number is 2

.. code-block:: console

    #ethtool -S eth0
    NIC statistics:
         rx_bytes: 0
         rx_unicast: 0
         rx_multicast: 0
         rx_broadcast: 0
         rx_discards: 0
         rx_unknown_protocol: 0
         tx_bytes: 70
         tx_unicast: 0
         tx_multicast: 1
         tx_broadcast: 0
         tx_discards: 0
         tx_errors: 0
         tx-0.packets: 2
         tx-0.bytes: 140
         tx-1.packets: 6
         tx-1.bytes: 1044
         rx-0.packets: 0
         rx-0.bytes: 0
         rx-1.packets: 0
         rx-1.bytes: 0

   Try to set VF Max possible RX queues and TX queues to 1/4/8/16 by PF,
   the VF rxq and txq number is 1/4/8/16::
