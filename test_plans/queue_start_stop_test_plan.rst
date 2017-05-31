.. Copyright (c) <2010-2017>, Intel Corporation
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

        $ ./testpmd -c 0xf -n 4 -- -i

Test Case: queue start/stop
---------------------------

This case support PF (fortville), VF (fortville,niantic)

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
