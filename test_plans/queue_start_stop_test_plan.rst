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

#. Compile testpmd again, then run testpmd.
#. Run "set fwd mac" to set fwd type
#. Run "start" to start fwd package
#. Start packet generator to transmit and receive packets
#. Run "port 0 rxq 0 stop" to stop rxq 0 in port 0
#. Start packet generator to transmit and not receive packets
#. Run "port 0 rxq 0 start" to start rxq 0 in port 0
#. Run "port 1 txq 1 stop" to start txq 0 in port 1
#. Start packet generator to transmit and not receive packets but in testpmd it is a "ports 0 queue 0 received 1 packages" print
#. Run "port 1 txq 1 start" to start txq 0 in port 1
#. Start packet generator to transmit and receive packets
#. Test it again with VF
