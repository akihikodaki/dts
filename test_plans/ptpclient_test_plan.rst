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

===============
EEE1588 Sample 
===============

The PTP (Precision Time Protocol) client sample application is a simple 
example of using the DPDK IEEE1588 API to communicate with a PTP master 
clock to synchronize the time on the NIC and, optionally, on the Linux 
system.

Prerequisites
=============
Assume one port are connected to the tester and tester has been installed
"linuxptp.x86_64".
The sample should be validated on Forville, Niantic and i350 Nics. 

Test case: ptp client
======================
Start ptp server on tester with IEEE 802.3 network transport::

    ptp4l -i p785p1 -2 -m

Start ptp client on DUT and wait few seconds::

    ./examples/ptpclient/build/ptpclient -c f -n 3 -- -T 0 -p 0x1

Check that output message contained T1,T2,T3,T4 clock and time difference
between master and slave time is about 10us in niantic, 20us in Fortville,
8us in i350.
   
Test case: update system
========================
Reset DUT clock to initial time and make sure system time has been changed::

    date -s "1970-01-01 00:00:00"    

Strip DUT and tester board system time::

    date +"%s.%N"

Start ptp server on tester with IEEE 802.3 network transport::

    ptp4l -i p785p1 -2 -m -S

Start ptp client on DUT and wait few seconds::

    ./examples/ptpclient/build/ptpclient -c f -n 3 -- -T 1 -p 0x1

Make sure DUT system time has been changed to same as tester.
Check that output message contained T1,T2,T3,T4 clock and time difference
between master and slave time is about 10us in niantic, 20us in Fortville,
8us in i350.
