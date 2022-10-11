.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

========================
Shutdown API Queue Tests
========================

This tests for Shutdown API feature can be run on linux userspace. It
will check if NIC port can be stopped and restarted without exiting the
application process. Furthermore, it will check if it can reconfigure
new configurations for a port after the port is stopped, and if it is
able to restart with those new configurations. It is based on testpmd
application.

The test is performed by running the testpmd application and using a
traffic generator. Port/queue configurations can be set interactively,
and still be set at the command line when launching the application in
order to be compatible with previous test framework.

Prerequisites
-------------

Assume port A and B are connected to the remote ports, e.g. packet generator.
To run the testpmd application in linuxapp environment with 4 lcores,
4 channels with other default parameters in interactive mode::

        $ ./<build_target>/app/dpdk-testpmd -c 0xf -n 4 -- -i

Test Case: queue start/stop
---------------------------

This case support PF (Intel® Ethernet 700 Series/Intel® Ethernet 800 Series/82599), VF (Intel® Ethernet 700 Series, 82599)

#. Update testpmd source code. Add the following C code in ./app/test-pmd/fwdmac.c::

      printf("ports %u queue %u received %u packages\n", fs->rx_port, fs->rx_queue, nb_rx);

#. Compile testpmd again, then run testpmd::
    x86_64-native-linuxapp-gcc/app/dpdk-testpmd  -l 1-2 -n 4 -a 0000:af:00.0 -- -i --portmask=0x1 --port-topology=loop

#. Run "set fwd mac" to set fwd type
#. Run "start" to start fwd package

#. Start a packet capture on the tester in the background::
    tcpdump -i ens7  'ether[12:2] != 0x88cc'  -Q in -w /tmp/tester/sniff_ens7.pcap

#. Start packet generator to transmit packets::
    sendp([Ether(dst='3c:fd:fe:c1:0f:4c', src='00:00:20:00:00:00')/IP()/UDP()/Raw(load=b'XXXXXXXXXXXXXXXXXX')],iface="ens7",count=4,inter=0,verbose=False)

#. Quit tcpdump and check tester port receive packets

#. Run "port 0 rxq 0 stop" to stop rxq 0 in port 0
#. Start packet generator to transmit and check tester port not receive packets

#. Run "port 0 rxq 0 start" to start rxq 0 in port 0
#. Run "port 0 txq 0 stop" to stop txq 0 in port 0
#. Start packet generator to transmit and check tester port not receive packets
   and in testpmd it not has "ports 0 queue 0 received 1 packages" print

#. Run "port 0 txq 0 start" to start txq 0 in port 0
#. Start packet generator to transmit and check tester port receive packets
   and in testpmd it has "ports 0 queue 0 received 1 packages" print
#. Test it again with VF
