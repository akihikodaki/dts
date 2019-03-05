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

=============
Dynamic queue 
=============
Currently, to configure a DPDK ethdev, the application first specifies 
how many Tx and Rx queues to include in the ethdev. The application then 
sets up each Tx and Rx queue. Finally, once all the queues have been set up, 
the application may then start the device, at this point traffic can flow. 
If device stops, this halts the flow of traffic on all queues in the ethdev, 
not one or part of all queues stop.

According to existing implementation, rte_eth_[rx|tx]_queue_setup will
always return fail if device is already started(rte_eth_dev_start).
This can't satisfy the usage when application wants to defer to setup
part of the queues while keeping traffic running on those queues already
be setup.

Basically this is not a general hardware limitation, because for NIC
like i40e, ixgbe, it is not necessary to stop the whole device before
configure a fresh queue or reconfigure an existing queue with no traffic
on it.

Dynamic queue lets etherdev driver exposes the capability flag through
rte_eth_dev_info_get when it supports deferred queue configuraiton,
then base on this flag, rte_eth_[rx|tx]_queue_setup could decide to
continue to setup the queue or just return fail when device already
started.

Allow ethdevs to setup/reconfigure/tear down queues at runtime without 
stopping the device. Given an ethdev configuration with a specified 
number of Tx and Rx queues, requirements as below:

1.The application should be able to start the device with only some of the 
queues set up.
2.The application should be able to set up additional queues at runtime 
without calling dev_stop().
3.The application should be able to reconfigure existing queues at runtime 
without calling dev_stop().
4.This support should be implemented in such a way that it does not break 
existing PMDs. 

Prerequisites
=============
1. Host PF in DPDK driver::

    ./usertools/dpdk-devbind.py -b igb_uio 81:00.0

2. Start testpmd on host, set chained port topology mode, add txq/rxq to 
   enable multi-queues::
   
    ./testpmd -c 0xf -n 4  -- -i --port-topology=chained --txq=64 --rxq=64


Test Case: Rx queue setup at runtime
====================================
Stop some Rx queues on port 0::

    testpmd> port 0 rxq <id> stop

Set rxonly forward, start testpmd

Send different src or dst IPv4 packets::

    p=Ether()/IP(src="192.168.0.1", dst="192.168.0.1")/Raw("x"*20)

Stop testpmd, find stopped queues can't receive packets, but other queues 
could receive packets
	
Setup these stopped queues on the port::

    testpmd> port 0 rxq <id> setup

Start these stopped queues on the port, start testpmd::

    testpmd> port 0 rxq <id> start

Send different src or dst IPv4 packets

Stop testpmd, check all the setup queues could receive packets


Test Case: Tx queue setup at runtime
====================================
Check txq ring size is 256::
                
    testpmd> show txq info 0 <id>
    Number of TXDs: 256

Stop one Tx queue on port 0::

    testpmd> port 0 txq <id> stop

Set txonly forward, start testpmd

Start testpmd, then stop, check this stopped queue only transmits 255 packets
  
Setup this stopped queue on the port::

    testpmd> port 0 txq <id> setup

Start this stopped queue on the port::

    testpmd> port 0 txq <id> start

Start then stop testpmd, check all queues could transmit lots of packets, 
not only 255 packets

Repeat above steps for 3 times


Test Case: Rx queue configure at runtime
========================================
Stop some Rx queues on port 0::

    testpmd> port 0 rxq <id> stop

Set rxonly forward, start testpmd

Send different src or dst IPv4 packets::

    p=Ether()/IP(src="192.168.0.1", dst="192.168.0.1")/Raw("x"*20)

Stop testpmd, find stopped queues can't receive packets, but other queues
could receive packets

Check rxq ring size is 256::
     
    testpmd> show rxq info 0 <id>
    Number of RXDs: 256

Reconfigure ring size as 512 for the stopped queues on port 0::

    testpmd> port config 0 rxq <id> ring_size 512

Setup these stopped queues on the port::

    testpmd> port 0 rxq <id> setup

Check stopped rxq ring sizes have been changed to 512

Start these stopped queues on the port, start testpmd::

    testpmd> port 0 rxq <id> start

Send different src or dst IPv4 packets

Stop testpmd, check all the setup queues could receive packets


Test Case: Tx queue configure at runtime
========================================
Check txq ring size is 256::

    testpmd> show txq info 0 <id>
    Number of TXDs: 256

Stop one Tx queue on port 0::

    testpmd> port 0 txq <id> stop

Set txonly forward, start testpmd

Start testpmd, then stop, check this stopped queue only transmits 255 packets

Reconfigure ring size as 512 for the stopped queues on port 0::

    testpmd> port config 0 txq <id> ring_size 512

Setup these stopped queues on the port::

    testpmd> port 0 txq <id> setup

Check stopped txq ring sizes have been changed to 512

Start these stopped queues on the port, start testpmd::

    testpmd> port 0 txq <id> start

Stop testpmd, check all queues could transmit lots of packets,
not only 511 packets

Repeat above steps for 3 times

