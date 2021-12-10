.. Copyright (c) <2016-2017>, Intel Corporation
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

========================================
VF RSS - Configuring Hash Function Tests
========================================

This document provides test plan for testing the function of Fortville:
Support configuring hash functions.

Prerequisites
-------------

Each of the Ethernet ports of the DUT is directly connected in full-duplex
to a different port of the peer traffic generator.

Network Traffic
---------------

The RSS feature is designed to improve networking performance by load balancing
the packets received from a NIC port to multiple NIC RX queues, with each queue
handled by a different logical core.

#. The receive packet is parsed into the header fields used by the hash
   operation (such as IP addresses, TCP port, etc.)

#. A hash calculation is performed. The Fortville supports three hash function:
   Toeplitz, simple XOR and their Symmetric RSS.

#. Hash results are used as an index into a 128/512 entry
   'redirection table'.

#. Niantic VF only supports simple default hash algorithm(simple). Fortville NICs
   support all hash algorithm only used dpdk driver on host. when used kernel driver on host,
   fortville NICs only support default hash algorithm(simple).

The RSS RETA update feature is designed to make RSS more flexible by allowing
users to define the correspondence between the seven LSBs of hash result and
the queue id(RSS output index) by themself.


Test Case:  test_rss_hash
=========================

The following RX Ports/Queues configurations have to be benchmarked:

- 1 RX port / 4 RX queues (1P/4Q)


Testpmd configuration - 4 RX/TX queues per port
-----------------------------------------------

::

  dpdk-testpmd -c 1f -n 3  -- -i --rxq=4 --txq=4 --tx-offloads=0x8fff

Testpmd Configuration Options
-----------------------------

By default, a single logical core runs the test.
The CPU IDs and the number of logical cores running the test in parallel can
be manually set with the ``set corelist X,Y`` and the ``set nbcore N``
interactive commands of the ``testpmd`` application.

1. Got the pci device id of DUT, for example::

     ./usertools/dpdk-devbind.py -s

     0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
     0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=

2. Create 2 VFs from 2 PFs::

     echo 1 > /sys/bus/pci/devices/0000\:81\:00.0/sriov_numvfs
     echo 1 > /sys/bus/pci/devices/0000\:81\:00.1/sriov_numvfs
     ./usertools/dpdk-devbind.py -s

     0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
     0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=
     0000:81:02.0 'XL710/X710 Virtual Function' unused=
     0000:81:0a.0 'XL710/X710 Virtual Function' unused=

3. Detach VFs from the host, bind them to pci-stub driver::

     /sbin/modprobe pci-stub

   using ``lspci -nn|grep -i ethernet`` got VF device id, for example "8086 154c"::

     echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
     echo 0000:81:02.0 > /sys/bus/pci/devices/0000:08:02.0/driver/unbind
     echo 0000:81:02.0 > /sys/bus/pci/drivers/pci-stub/bind

     echo "8086 154c" > /sys/bus/pci/drivers/pci-stub/new_id
     echo 0000:81:0a.0 > /sys/bus/pci/devices/0000:08:0a.0/driver/unbind
     echo 0000:81:0a.0 > /sys/bus/pci/drivers/pci-stub/bind

  or using the following more easy way::

     virsh nodedev-detach pci_0000_81_02_0;
     virsh nodedev-detach pci_0000_81_0a_0;

     ./usertools/dpdk-devbind.py -s

     0000:81:00.0 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f0 drv=i40e unused=
     0000:81:00.1 'Ethernet Controller X710 for 10GbE SFP+' if=ens259f1 drv=i40e unused=
     0000:81:02.0 'XL710/X710 Virtual Function' if= drv=pci-stub unused=
     0000:81:0a.0 'XL710/X710 Virtual Function' if= drv=pci-stub unused=

  it can be seen that VFs 81:02.0 & 81:0a.0 's drv is pci-stub.

4. Passthrough VFs 81:02.0 & 81:0a.0 to vm0, and start vm0::

     /usr/bin/qemu-system-x86_64  -name vm0 -enable-kvm \
     -cpu host -smp 4 -m 2048 -drive file=/home/image/sriov-fc20-1.img -vnc :1 \
     -device pci-assign,host=81:02.0,id=pt_0 \
     -device pci-assign,host=81:0a.0,id=pt_1

5. Login vm0, got VFs pci device id in vm0, assume they are 00:06.0 & 00:07.0,
   bind them to igb_uio driver, and then start testpmd, set it in mac forward
   mode::

    ./usertools/dpdk-devbind.py --bind=igb_uio 00:06.0 00:07.0

6. Pmd fwd only receive the packets::

     testpmd command: set fwd rxonly

7. Rss received package type configuration two received packet types configuration::

     testpmd command: port config all rss ip/udp/tcp

8. Verbose configuration::

     testpmd command: set verbose 8

9. Start packet receive::

      testpmd command: start

10. Send different hash types' packets with different keywords, then check rx port
    could receive packets by different queues::

      sendp([Ether(dst="90:e2:ba:36:99:3c")/IP(src="192.168.0.4", dst="192.168.0.5")], iface="eth3")
      sendp([Ether(dst="90:e2:ba:36:99:3c")/IP(src="192.168.0.5", dst="192.168.0.4")], iface="eth3")

Test Case:  test_reta
=====================

This case test hash reta table, the test steps same with test_rss_hash except config hash reta table

Before send packet, config hash reta,512(NICS with kernel driver i40e has 64 reta) reta entries configuration::

  testpmd command: port config 0 rss reta (hash_index,queue_id)

after send packet, based on the testpmd output RSS hash value to calculate hash_index, then check whether the
actual receive queue is the queue configured in the reta.
