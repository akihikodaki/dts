.. Copyright (c) <2019>, Intel Corporation
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

==================
Port Control Tests
==================


Prerequisites
=============

1. Hardware:

   * Fortville
   * Niantic
   * Columbiaville
   * i350 NIC
   * e1000 emulated device


Test Case: pf start/stop/reset/close
====================================

1. Bind the port to dpdk driver::

     ./usertools/dpdk-devbind.py -b igb_uio 18:00.2

2. Run testpmd::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xff -n 4 -- -i

     testpmd> set fwd mac
     testpmd> start

   check port info::

     testpmd> show port info all

     ********************* Infos for port 0  *********************
     Link status: up
     Link speed: 1000 Mbps

   verify that the link status is up.

   Using scapy to send 1000 random packets from tester,
   verify the packets can be received and can be forwarded::

     scapy
     >>>sendp([Ether(dst="00:11:22:33:44:11")/IP()/Raw('x'*40)], \
     iface="enp27s0f2",count=1000)

3. Stop and start port::

     testpmd> stop
     testpmd> port stop all
     testpmd> show port info all

     ********************* Infos for port 0  *********************
     Link status: down
     Link speed: 0 Mbps

  verify that the link status is down.

  Then start the port::

    testpmd> port start all
    testpmd> start

  check port info::

    testpmd> show port info all

    ********************* Infos for port 0  *********************
    Link status: up
    Link speed: 10000 Mbps

  verify that the link status is up.

  Send the same 1000 packets with scapy from tester,
  verify the packets can be received and forwarded.

4. Reset the port, run the commands::

     testpmd> stop
     testpmd> port stop all
     testpmd> port reset all
     testpmd> show port info all

     ********************* Infos for port 0  *********************
     Link status: down
     Link speed: 0 Mbps

   verify that the link status is down.

   Then start the port::

     testpmd> port start all
     testpmd> start

   check port info::

     testpmd> show port info all

     ********************* Infos for port 0  *********************
     Link status: up
     Link speed: 10000 Mbps

   verify that the link status is up.
   Send the same 1000 packets with scapy from tester,
   verify the packets can be received and forwarded.

5. Close the port, run the commands::

     testpmd> stop
     testpmd> port stop all
     testpmd> port close all

   check the port info::

     testpmd> show port info all
     testpmd>

   verify that there is no output after executing this command.


Test Case: e1000 emulated device start/stop/reset/close
=======================================================

1. Set up qemu environment

   Virtual an e1000 emulated device in vm, then start
   vm with the following command::

     qemu-system-x86_64 -enable-kvm -m 16G -vnc :20 \
     -smp cores=10,sockets=1 -cpu host -hda ./u18.img \
     -device e1000,netdev=net1,mac=00:01:02:33:44:22 \
     -netdev user,id=net1,hostfwd=tcp:10.67.119.144:6666-:22 \
     -device e1000,netdev=net2,mac=00:01:02:33:44:33 \
     -netdev user,id=net2,hostfwd=tcp:10.67.119.144:7777-:23 \
     -monitor stdio

   Login vm, get the pci device id of the e1000 emulated device,
   assume it is 0000:00:03.0, bind it to igb_uio driver, and then
   start testpmd::

     ./usertools/dpdk-devbind.py -b igb_uio 0000:00:03.0
     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -- -i

     testpmd-> set fwd mac
     testpmd-> start

   check port info::

     testpmd> show port info all

     ********************* Infos for port 0  *********************
     Link status: up
     Link speed: 1000 Mbps

   verify that the link status is up.

2. Stop and start port (not support)::

     testpmd> stop
     testpmd> port stop all
     testpmd> show port info all

     ********************* Infos for port 0  *********************
     Link status: down
     Link speed: 0 Mbps

   verify that the link status is down.

   Then start the port::

     testmd-> port start all
     testpmd> start

   check the port info::

      testpmd> show port info all

      ********************* Infos for port 0  *********************
      Link status: up
      Link speed: 10000 Mbps

   verify that the link status is up.

3. Reset the port (not support)::

     testpmd> stop
     testpmd> port stop all
     testpmd> port reset all
     testpmd> show port info all

     ********************* Infos for port 0  *********************
     Link status: down
     Link speed: 0 Mbps

   verify that the link status is down.

   Then start the port::

     testpmd> port start all
     testpmd> start

   check the port info::

      testpmd> show port info all

      ********************* Infos for port 0  *********************
      Link status: up
      Link speed: 10000 Mbps

   verify that the link status is up.

4. Close the port::

     testpmd> stop
     testpmd> port stop all
     testpmd> port close all

   check the port info::

     testpmd> show port info all
     testpmd>

   verify that there is no output after executing this command.
