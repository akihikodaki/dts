.. Copyright (c) <2022>, Intel Corporation
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


=======================================
Sample Application Tests: Multi-Process
=======================================

Simple MP Application Test
==========================

Description
-----------

This test is a basic multi-process test for iavf which demonstrates the basics of sharing
information between DPDK processes. The same application binary is run
twice - once as a primary instance, and once as a secondary instance. Messages
are sent from primary to secondary and vice versa, demonstrating the processes
are sharing memory and can communicate using rte_ring structures.

Prerequisites
-------------

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   echo 1 > /sys/bus/pci/devices/0000:17:00.0/sriov_numvfs
   ip link set ens9 vf0 mac 00:11:22:33:44:55
   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci {vf_pci}

Assuming that a DPDK build has been set up and the multi-process sample
applications have been built.

Test Case: Basic operation
--------------------------

1. To run the application, start one copy of the simple_mp binary in one terminal,
   passing at least two cores in the coremask, as follows::

       ./x86_64-native-linuxapp-gcc/examples/dpdk-simple_mp -c 3 --proc-type=primary

   The process should start successfully and display a command prompt as follows::

       $ ./x86_64-native-linuxapp-gcc/examples/dpdk-simple_mp -c 3 --proc-type=primary
       EAL: coremask set to 3
       EAL: Detected lcore 0 on socket 0
       EAL: Detected lcore 1 on socket 0
       EAL: Detected lcore 2 on socket 0
       EAL: Detected lcore 3 on socket 0
       ...
       EAL: Requesting 2 pages of size 1073741824
       EAL: Requesting 768 pages of size 2097152
       EAL: Ask a virtual area of 0x40000000 bytes
       EAL: Virtual area found at 0x7ff200000000 (size = 0x40000000)
       ...
       EAL: check igb_uio module
       EAL: check module finished
       EAL: Master core 0 is ready (tid=54e41820)
       EAL: Core 1 is ready (tid=53b32700)
       Starting core 1

       simple_mp >

2. To run the secondary process to communicate with the primary process, again run the
   same binary setting at least two cores in the coremask.::

       ./x86_64-native-linuxapp-gcc/examples/dpdk-simple_mp -c C --proc-type=secondary

   Once the process type is specified correctly, the process starts up, displaying largely
   similar status messages to the primary instance as it initializes. Once again, you will be
   presented with a command prompt.

3. Once both processes are running, messages can be sent between them using the send
   command. At any stage, either process can be terminated using the quit command.

   Validate that this is working by sending a message between each process, both from
   primary to secondary and back again. This is shown below.

   Transcript from the primary - text entered by used shown in ``{}``::

       EAL: Master core 10 is ready (tid=b5f89820)
       EAL: Core 11 is ready (tid=84ffe700)
       Starting core 11
       simple_mp > {send hello_secondary}
       simple_mp > core 11: Received 'hello_primary'
       simple_mp > {quit}

   Transcript from the secondary - text entered by the user is shown in ``{}``::

       EAL: Master core 8 is ready (tid=864a3820)
       EAL: Core 9 is ready (tid=85995700)
       Starting core 9
       simple_mp > core 9: Received 'hello_secondary'
       simple_mp > {send hello_primary}
       simple_mp > {quit}

Test Case: Load test of Simple MP application
---------------------------------------------

1. Start up the sample application using the commands outlined in steps 1 & 2
   above.

2. To load test, send a large number of strings (>5000), from the primary instance
   to the secondary instance, and then from the secondary instance to the primary.
   [NOTE: A good source of strings to use is /usr/share/dict/words which contains
   >400000 ascii strings on Fedora 14]

Test Case: Test use of Auto for Application Startup
---------------------------------------------------

1. Start the primary application as in Test 1, Step 1, except replace
   ``--proc-type=primary`` with ``--proc-type=auto``

2. Validate that the application prints the line:
   ``EAL: Auto-detected process type: PRIMARY`` on startup.

3. Start the secondary application as in Test 1, Step 2, except replace
   ``--proc-type=secondary`` with ``--proc-type=auto``.

4. Validate that the application prints the line:
   ``EAL: Auto-detected process type: SECONDARY`` on startup.

5. Verify that processes can communicate by sending strings, as in Test 1,
   Step 3.

Test Case: Test running multiple processes without "--proc-type" flag
---------------------------------------------------------------------

1. Start up the primary process as in Test 1, Step 1, except omit the
   ``--proc-type`` flag completely.

2. Validate that process starts up as normal, and returns the ``simple_mp>``
   prompt.

3. Start up the secondary process as in Test 1, Step 2, except omit the
   ``--proc-type`` flag.

4. Verify that the process *fails* to start and prints an error message as
   below::

      "PANIC in rte_eal_config_create():
      Cannot create lock on '/path/to/.rte_config'. Is another primary process running?"

Symmetric MP Application Test
=============================

Description
-----------

This test is a multi-process test which demonstrates how multiple processes can
work together to perform packet I/O and packet processing in parallel, much as
other example application work by using multiple threads. In this example, each
process reads packets from all network ports being used - though from a different
RX queue in each case. Those packets are then forwarded by each process which
sends them out by writing them directly to a suitable TX queue.

Prerequisites
-------------

Assuming that an Intel DPDK build has been set up and the multi-process sample
applications have been built. It is also assumed that a traffic generator has
been configured and plugged in to the NIC ports 0 and 1.

Test Methodology
----------------

As with the simple_mp example, the first instance of the symmetric_mp process
must be run as the primary instance, though with a number of other application
specific parameters also provided after the EAL arguments. These additional
parameters are:

* -p <portmask>, where portmask is a hexadecimal bitmask of what ports on the
  system are to be used. For example: -p 3 to use ports 0 and 1 only.
* --num-procs <N>, where N is the total number of symmetric_mp instances that
  will be run side-by-side to perform packet processing. This parameter is used to
  configure the appropriate number of receive queues on each network port.
* --proc-id <n>, where n is a numeric value in the range 0 <= n < N (number of
  processes, specified above). This identifies which symmetric_mp instance is being
  run, so that each process can read a unique receive queue on each network port.

The secondary symmetric_mp instances must also have these parameters specified,
and the first two must be the same as those passed to the primary instance, or errors
result.

For example, to run a set of four symmetric_mp instances, running on lcores 1-4, all
performing level-2 forwarding of packets between ports 0 and 1, the following
commands can be used (assuming run as root)::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-symmetric_mp -c 2 --proc-type=auto -- -p 3 --num-procs=4 --proc-id=0
   ./x86_64-native-linuxapp-gcc/examples/dpdk-symmetric_mp -c 4 --proc-type=auto -- -p 3 --num-procs=4 --proc-id=1
   ./x86_64-native-linuxapp-gcc/examples/dpdk-symmetric_mp -c 8 --proc-type=auto -- -p 3 --num-procs=4 --proc-id=2
   ./x86_64-native-linuxapp-gcc/examples/dpdk-symmetric_mp -c 10 --proc-type=auto -- -p 3 --num-procs=4 --proc-id=3

To run only 1 or 2 instances, the above parameters to the 1 or 2 instances being
run should remain the same, except for the ``num-procs`` value, which should be
adjusted appropriately.


Test Case: Function Tests
-------------------------
start 2 symmetric_mp process, send some packets, the number of packets is a random value between 20 and 256.
summarize all received packets and check whether it is bigger than or equal to the number of sent packets

1. start 2 process::

    /dpdk-symmetric_mp  -l 1 -n 4 --proc-type=auto  -a 0000:05:01.0 -a 0000:05:01.1 -- -p 0x3 --num-procs=2 --proc-id=0
    /dpdk-symmetric_mp  -l 2 -n 4 --proc-type=auto  -a 0000:05:01.0 -a 0000:05:01.1 -- -p 0x3 --num-procs=2 --proc-id=1

2. send some packets,the number of packets is a random value between 20 and 256, packet type including IPV6/4,TCP/UDP,
   refer to Random_Packet

3. stop all process and check output::

    the number of received packets for each process should bigger than 0.
    summarize all received packets for all process should bigger than or equal to the number of sent packets


Client Server Multiprocess Tests
================================

Description
-----------

The client-server sample application demonstrates the ability of Intel� DPDK
to use multiple processes in which a server process performs packet I/O and one
or multiple client processes perform packet processing. The server process
controls load balancing on the traffic received from a number of input ports to
a user-specified number of clients. The client processes forward the received
traffic, outputting the packets directly by writing them to the TX rings of the
outgoing ports.

Prerequisites
-------------

Assuming that an Intel� DPDK build has been set up and the multi-process
sample application has been built.
Also assuming a traffic generator is connected to the ports "0" and "1".

It is important to run the server application before the client application,
as the server application manages both the NIC ports with packet transmission
and reception, as well as shared memory areas and client queues.

Run the Server Application:

- Provide the core mask on which the server process is to run using -c, e.g. -c 3 (bitmask number).
- Set the number of ports to be engaged using -p, e.g. -p 3 refers to ports 0 & 1.
- Define the maximum number of clients using -n, e.g. -n 8.

The command line below is an example on how to start the server process on
logical core 2 to handle a maximum of 8 client processes configured to
run on socket 0 to handle traffic from NIC ports 0 and 1::

    root@host:mp_server# ./x86_64-native-linuxapp-gcc/examples/dpdk-mp_server -c 2 -- -p 3 -n 8

NOTE: If an additional second core is given in the coremask to the server process
that second core will be used to print statistics. When benchmarking, only a
single lcore is needed for the server process

Run the Client application:

- In another terminal run the client application.
- Give each client a distinct core mask with -c.
- Give each client a unique client-id with -n.

An example commands to run 8 client processes is as follows::

   root@host:mp_client# ./x86_64-native-linuxapp-gcc/examples/dpdk-mp_client -c 40 --proc-type=secondary -- -n 0 &
   root@host:mp_client# ./x86_64-native-linuxapp-gcc/examples/dpdk-mp_client -c 100 --proc-type=secondary -- -n 1 &
   root@host:mp_client# ./x86_64-native-linuxapp-gcc/examples/dpdk-mp_client -c 400 --proc-type=secondary -- -n 2 &
   root@host:mp_client# ./x86_64-native-linuxapp-gcc/examples/dpdk-mp_client -c 1000 --proc-type=secondary -- -n 3 &
   root@host:mp_client# ./x86_64-native-linuxapp-gcc/examples/dpdk-mp_client -c 4000 --proc-type=secondary -- -n 4 &
   root@host:mp_client# ./x86_64-native-linuxapp-gcc/examples/dpdk-mp_client -c 10000 --proc-type=secondary -- -n 5 &
   root@host:mp_client# ./x86_64-native-linuxapp-gcc/examples/dpdk-mp_client -c 40000 --proc-type=secondary -- -n 6 &
   root@host:mp_client# ./x86_64-native-linuxapp-gcc/examples/dpdk-mp_client -c 100000 --proc-type=secondary -- -n 7 &

Test Case: Function Tests
-------------------------
start server process and 2 client process, send some packets, the number of packets is a random value between 20 and 256.
summarize all received packets and check whether it is bigger than or equal to the number of sent packets

1. start server process::

    ./dpdk-mp_server  -l 1,2 -n 4 -a 0000:05:01.0 -a 0000:05:01.1 -- -p 0x3 -n 2

2. start 2 client process::

    ./dpdk-mp_client  -l 3 -n 4 -a 0000:05:01.0 -a 0000:05:01.1 --proc-type=auto -- -n 0
    ./dpdk-mp_client  -l 4 -n 4 -a 0000:05:01.0 -a 0000:05:01.1 --proc-type=auto -- -n 1

3. send some packets,the number of packets is a random value between 20 and 256, packet type include IPV6/4,TCP/UDP,
   refer to Random_Packet

4. stop all process and check output::

    the number of received packets for each client should bigger than 0.
    summarize all received packets for all clients should bigger than or equal to the number of sent packets

Testpmd Multi-Process Test
==========================

Description
-----------

This is a multi-process test for Testpmd application, which demonstrates how multiple processes can
work together to perform packet in parallel.

Test Methodology
----------------
Testpmd support to specify total number of processes and current process ID.
Each process owns subset of Rx and Tx queues
The following are the command-line options for testpmd multi-process support::

   primary process:
   ./dpdk-testpmd -a xxx --proc-type=auto -l 0-1 -- -i --rxq=4 --txq=4 --num-procs=2 --proc-id=0

   secondary process:
   ./dpdk-testpmd -a xxx --proc-type=auto -l 2-3 -- -i --rxq=4 --txq=4 --num-procs=2 --proc-id=1

   --num-procs:
      The number of processes which will be used
   --proc-id:
      The ID of the current process (ID < num-procs),ID should be different in primary process and secondary
      process, which starts from ‘0’.

All queues are allocated to different processes based on proc_num and proc_id
Calculation rule for queue::

   start(queue start id) = proc_id * nb_q / num_procs
   end(queue end id) = start + nb_q / num_procs

For example, if testpmd is configured to have 4 Tx and Rx queues, queues 0 and 1 will be used by the primary process and
queues 2 and 3 will be used by the secondary process.

Note::

   nb_q is the number of queue
   The number of queues should be a multiple of the number of processes. If not, redundant queues will exist after
   queues are allocated to processes. If RSS is enabled, packet loss occurs when traffic is sent to all processes at the
   same time.Some traffic goes to redundant queues and cannot be forwarded.
   All the dev ops is supported in primary process. While secondary process is not permitted to allocate or release
   shared memory.
   When secondary is running, port in primary is not permitted to be stopped.
   Reconfigure operation is only valid in primary.
   Stats is supported, stats will not change when one quits and starts, as they share the same buffer to store the stats.
   Flow rules are maintained in process level:
      primary and secondary has its own flow list (but one flow list in HW). The two can see all the queues, so setting
      the flow rules for the other is OK. But in the testpmd primary process receiving or transmitting packets from the
      queue allocated for secondary process is not permitted, and same for secondary process

   Flow API and RSS are supported

Prerequisites
-------------

1. Hardware:
   Intel® Ethernet 800 Series: E810-CQDA2/E810-2CQDA2/E810-XXVDA4 etc

2. Software:
   DPDK: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Copy specific ice package to /lib/firmware/intel/ice/ddp/ice.pkg

4. Generate 2 VFs on PF and set mac address for vf0::

    echo 2 > /sys/bus/pci/devices/0000:af:00.0/sriov_numvfs
    ip link set eth7 vf 0 mac 00:11:22:33:44:55

   0000:05:00.0 generate 0000:05:01.0 and 0000:05:01.1

4. Bind VFs to dpdk driver::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:05:01.0  0000:05:01.1

Default parameters
------------------

   MAC::

    [Dest MAC]: 00:11:22:33:44:55

   IPv4::

    [Source IP]: 192.168.0.20
    [Dest IP]: 192.168.0.21
    [IP protocol]: 255
    [TTL]: 2
    [DSCP]: 4

   TCP::

    [Source Port]: 22
    [Dest Port]: 23

   Random_Packet::

    Ether(dst='00:11:22:33:44:55', src='00:00:20:00:00:00')/IPv6(src='::192.168.0.1', version=6, tc=0, fl=0, dst='::192.168.1.1', hlim=64)/TCP(sport=65535, dport=65535, flags=0)/Raw(),
    Ether(dst='00:11:22:33:44:55', src='00:00:20:00:00:00')/IP(frag=0, src='192.168.0.1', tos=0, dst='192.168.1.2', version=4, ttl=64, id=1)/UDP(sport=65535, dport=65535)/Raw(),
    Ether(dst='00:11:22:33:44:55', src='00:00:20:00:00:00')/IPv6(src='::192.168.0.1', version=6, tc=0, fl=0, dst='::192.168.1.3', hlim=64)/UDP(sport=65535, dport=65535)/Raw(),
    Ether(dst='00:11:22:33:44:55', src='00:00:20:00:00:00')/IPv6(src='::192.168.0.1', version=6, tc=0, fl=0, dst='::192.168.1.4', hlim=64)/UDP(sport=65535, dport=65535)/Raw(),
    Ether(dst='00:11:22:33:44:55', src='00:00:20:00:00:00')/IPv6(src='::192.168.0.1', version=6, tc=0, fl=0, dst='::192.168.1.5', hlim=64)/TCP(sport=65535, dport=65535, flags=0)/Raw(),
    Ether(dst='00:11:22:33:44:55', src='00:00:20:00:00:00')/IP(frag=0, src='192.168.0.1', tos=0, dst='192.168.1.15', version=4, ttl=64, id=1)/UDP(sport=65535, dport=65535)/Raw(),
    Ether(dst='00:11:22:33:44:55', src='00:00:20:00:00:00')/IPv6(src='::192.168.0.1', version=6, tc=0, fl=0, dst='::192.168.1.16', hlim=64)/TCP(sport=65535, dport=65535, flags=0)/Raw(),
    Ether(dst='00:11:22:33:44:55', src='00:00:20:00:00:00')/IPv6(src='::192.168.0.1', version=6, tc=0, fl=0, dst='::192.168.1.27', hlim=64)/TCP(sport=65535, dport=65535, flags=0)/Raw(),
    Ether(dst='00:11:22:33:44:55', src='00:00:20:00:00:00')/IP(frag=0, src='192.168.0.1', tos=0, dst='192.168.1.28', version=4, ttl=64, id=1)/TCP(sport=65535, dport=65535, flags=0)/Raw(),
    Ether(dst='00:11:22:33:44:55', src='00:00:20:00:00:00')/IPv6(src='::192.168.0.1', version=6, tc=0, fl=0, dst='::192.168.1.30', hlim=64)/TCP(sport=65535, dport=65535, flags=0)/Raw()

Test Case: multiprocess proc_type random packet
===============================================

Subcase 1: proc_type_auto_4_process
-----------------------------------
1. Launch the app ``testpmd``, start 4 process with rxq/txq set as 16 (proc_id:0~3, queue id:0~15) with the following arguments::

   ./dpdk-testpmd -l 1,2 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=16 --txq=16 --num-procs=4 --proc-id=0
   ./dpdk-testpmd -l 3,4 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=16 --txq=16 --num-procs=4 --proc-id=1
   ./dpdk-testpmd -l 5,6 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=16 --txq=16 --num-procs=4 --proc-id=2
   ./dpdk-testpmd -l 7,8 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=16 --txq=16 --num-procs=4 --proc-id=3

2. Send 20 random packets::

    packets generated by script, packet type including 'TCP', 'UDP', 'IPv6_TCP', 'IPv6_UDP', like as: Random_Packet

3. Check whether each process receives 5 packets with the corresponding queue::

    process 0 should receive 5 packets with queue 0~3
    process 1 should receive 5 packets with queue 4~7
    process 2 should receive 5 packets with queue 8~11
    process 3 should receive 5 packets with queue 12~15

4. Check the statistics is correctly, the total number of packets received is 20

Subcase 2: proc_type_primary_secondary_2_process
------------------------------------------------
1. Launch the app ``testpmd``, start 2 process with rxq/txq set as 4 (proc_id:0~1, queue id:0~3) with the following arguments::

   ./dpdk-testpmd -l 1,2 --proc-type=primary -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=4 --txq=4 --num-procs=2 --proc-id=0
   ./dpdk-testpmd -l 3,4 --proc-type=secondary -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=4 --txq=4 --num-procs=2 --proc-id=1

2. Send 20 random packets::

    packets generated by script, packet type including 'TCP', 'TCP', 'IPv6_TCP', 'IPv6_UDP', such as: Random_Packet

3. Check whether each process receives 10 packets with the corresponding queue::

    process 0 should receive 10 packets with queue 0~1
    process 1 should receive 10 packets with queue 2~3


4. Check the statistics is correctly, the total number of packets received is 20

Test Case: multiprocess proc_type specify packet
================================================

Subcase 1: proc_type_auto_2_process
-----------------------------------
1. Launch the app ``testpmd``, start 2 process with rxq/txq set as 8 (proc_id:0~1, queue id:0~7) with the following arguments::

   ./dpdk-testpmd -l 1,2 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=8 --txq=8 --num-procs=2 --proc-id=0
   ./dpdk-testpmd -l 3,4 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=8 --txq=8 --num-procs=2 --proc-id=1

2. Create rule to set queue as one of each process queues::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20  / end actions queue index 0 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.1.20  / end actions queue index 1 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.2.20 / end actions queue index 2 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.3.20 / end actions queue index 3 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.4.20  / end actions queue index 4 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.5.20 / end actions queue index 5 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.6.20 / end actions queue index 6 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.7.20 / end actions queue index 7 / end

3. Send 1 matched packet for each rule::

    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20")/("X"*46)
    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.20")/("X"*46)
    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.2.20")/("X"*46)
    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.3.20")/("X"*46)
    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.4.20")/("X"*46)
    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.5.20")/("X"*46)
    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.6.20")/("X"*46)
    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.7.20")/("X"*46)

4. Check whether each process receives 4 packets with the corresponding queue::

    process 0 should receive 4 packets with queue 0~3
    process 1 should receive 4 packets with queue 4~7

5. Check the statistics is correctly, the total number of packets received is 8

Subcase 2: proc_type_primary_secondary_3_process
------------------------------------------------
1. Launch the app ``testpmd``, start 3 process with rxq/txq set as 6 (proc_id:0~2, queue id:0~5) with the following arguments::

   ./dpdk-testpmd -l 1,2 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=6 --txq=6 --num-procs=3 --proc-id=0
   ./dpdk-testpmd -l 3,4 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=6 --txq=6 --num-procs=3 --proc-id=1
   ./dpdk-testpmd -l 5,6 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=6 --txq=6 --num-procs=3 --proc-id=2

2. Create rule to set queue as one of each process queues::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20  / end actions queue index 0 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.1.20  / end actions queue index 1 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.2.20 / end actions queue index 2 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.3.20 / end actions queue index 3 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.4.20  / end actions queue index 4 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.5.20 / end actions queue index 5 / end

3. Send 1 matched packet for each rule::

    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20")/("X"*46)
    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.20")/("X"*46)
    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.2.20")/("X"*46)
    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.3.20")/("X"*46)
    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.4.20")/("X"*46)
    Ether(dst="00:11:22:33:44:55")/IP(src="192.168.5.20")/("X"*46)

4. Check whether each process receives 2 packets with the corresponding queue::

    process 0 should receive 2 packets with queue 0~1
    process 1 should receive 2 packets with queue 2~3
    process 2 should receive 2 packets with queue 4~5

5. Check the statistics is correctly, the total number of packets received is 6

Test Case: test_multiprocess_with_fdir_rule
===========================================

Launch the app ``testpmd``, start 2 process with rxq/txq set as 16 (proc_id:0~1, queue id:0~15) with the following arguments::

   ./dpdk-testpmd -l 1,2 -n 4 -a 0000:05:01.0 --proc-type=auto  --log-level=ice,7 -- -i --rxq=16 --txq=16  --num-procs=2 --proc-id=0
   ./dpdk-testpmd -l 3,4 -n 4 -a 0000:05:01.0 --proc-type=auto  --log-level=ice,7 -- -i --rxq=16 --txq=16  --num-procs=2 --proc-id=1

Subcase 1: mac_ipv4_pay_queue_index
-----------------------------------

1. Create rule::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 6 / mark id 4 / end

2. Send matched packets, check the packets is distributed to queue 6 with FDIR matched ID=0x4.
   Send unmatched packets, check the packets are distributed by RSS without FDIR matched ID

3. Verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. Verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 2: mac_ipv4_pay_rss_queues
----------------------------------
1. Create rule::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 10 11 end / mark / end

2. Send matched packets, check the packets is distributed to queue 10 or 11.
   Send unmatched packets, check the packets are distributed by RSS

3. Repeat step 3 of subcase 1

4. Verify matched packet is distributed by RSS.
   check there is no rule listed.

Subcase 3: mac_ipv4_pay_drop
----------------------------

1. Create rule::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions drop / mark / end

2. Send matched packets, check the packets are dropped.
   Send unmatched packets, check the packets are not dropped

3. Repeat step 3 of subcase 1

4. Verify matched packets are not dropped.
   check there is no rule listed.

Subcase 4: mac_ipv4_pay_mark_rss
--------------------------------
1. Create rule::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark / rss / end

2. Send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   Send unmatched packets, check the packets are distributed by RSS without FDIR matched ID

3. Repeat step 3 of subcase 1

4. Verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Note: step2 and step4 need to check whether all received packets of each process are distributed by RSS


Test Case: test_multiprocess_with_rss_toeplitz
==============================================
Launch the app ``testpmd``,start 2 process with queue num set as 16 (proc_id: 0~1, queue id: 0~15) with the following arguments::

    ./dpdk-testpmd -l 1,2 -n 4 -a 0000:05:01.0 --proc-type=auto  --log-level=ice,7 -- -i --rxq=16 --txq=16  --num-procs=2 --proc-id=0
    ./dpdk-testpmd -l 3,4 -n 4 -a 0000:05:01.0 --proc-type=auto  --log-level=ice,7 -- -i --rxq=16 --txq=16  --num-procs=2 --proc-id=1

all the test cases run the same test steps as below::

    1. validate rule.
    2. create rule and list rule.
    3. send a basic hit pattern packet,record the hash value,
       check the packet is distributed to queues by RSS.
    4. send hit pattern packet with changed input set in the rule.
       check the received packet have different hash value with basic packet.
       check the packet is distributed to queues by rss.
    5. send hit pattern packet with changed input set not in the rule.
       check the received packet have same hash value with the basic packet.
       check the packet is distributed to queues by rss.
    6. destroy the rule and list rule.
    7. send same packet with step 3.
       check the received packets have no hash value, and distributed to queue 0.

    Note: step3, step4 and step5 need to check whether all received packets of each process are distributed by RSS

basic hit pattern packets are the same in this test case.
ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

Subcase 1: mac_ipv4_tcp_l2_src
------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types eth l2-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:27:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=25,dport=99)/("X"*480)],iface="ens786f0")

Subcase: mac_ipv4_tcp_l2_dst
----------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types eth l2-dst-only end key_len 0 queues end / end

2. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=25,dport=99)/("X"*480)],iface="ens786f0")

Subcase: mac_ipv4_tcp_l2src_l2dst
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types eth end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", dst="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=25,dport=99)/("X"*480)],iface="ens786f0")

Subcase: mac_ipv4_tcp_l3_src
----------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)],iface="ens786f0")

Subcase: mac_ipv4_tcp_l3_dst
----------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=33)/("X"*480)],iface="ens786f0")

Subcase: mac_ipv4_tcp_l3src_l4src
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

Subcase: mac_ipv4_tcp_l3src_l4dst
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

Subcase: mac_ipv4_tcp_l3dst_l4src
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

Subcase: mac_ipv4_tcp_l3dst_l4dst
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

Subcase: mac_ipv4_tcp_l4_src
----------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.1.2")/TCP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

Subcase: mac_ipv4_tcp_l4_dst
----------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.1.2")/TCP(sport=32,dport=23)/("X"*480)],iface="ens786f0")

Subcase: mac_ipv4_tcp_ipv4
--------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")

Subcase: mac_ipv4_tcp_all
-------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

3. hit pattern/not defined input set:
ipv4-tcp packets::

    sendp([Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

Test Case: test_multiprocess_with_rss_symmetric
===============================================
Launch the app ``testpmd``, start 2 process with queue num set as 16(proc_id: 0~1, queue id: 0~15) with the following arguments::

    ./dpdk-testpmd -l 1,2 -n 4 -a 0000:05:01.0 --proc-type=auto  --log-level=ice,7 -- -i --rxq=16 --txq=16  --num-procs=2 --proc-id=0
    ./dpdk-testpmd -l 3,4 -n 4 -a 0000:05:01.0 --proc-type=auto  --log-level=ice,7 -- -i --rxq=16 --txq=16  --num-procs=2 --proc-id=1

test steps as below::

    1. validate and create rule.
    2. set "port config all rss all".
    3. send hit pattern packets with switched value of input set in the rule.
       check the received packets have the same hash value.
       check all the packets are distributed to queues by rss
    4. destroy the rule and list rule.
    5. send same packets with step 3
       check the received packets have no hash value, or have different hash value.

    Note: step3 needs to check whether all received packets of each process are distributed by RSS

Subcase: mac_ipv4_symmetric
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)],iface="ens786f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1",frag=6)/("X"*480)],iface="ens786f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="ens786f0")

Test Case: test_multiprocess_auto_process_type_detected
=======================================================
1. start 2 process with queue num set as 8 (proc_id:0~1,queue id:0~7)::

   ./dpdk-testpmd -l 1,2 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=8 --txq=8 --num-procs=2 --proc-id=0
   ./dpdk-testpmd -l 3,4 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=8 --txq=8 --num-procs=2 --proc-id=1

2. check the ouput of each process::

    process 1 output contains 'Auto-detected process type: PRIMARY'
    process 2 output contains 'Auto-detected process type: SECONDARY'

Test Case: test_multiprocess_negative_2_primary_process
=======================================================
1. start 2 process with queue num set as 4 (proc_id:0~1,queue id:0~3)::

   ./dpdk-testpmd -l 1,2 --proc-type=primary -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=4 --txq=4 --num-procs=2 --proc-id=0
   ./dpdk-testpmd -l 3,4 --proc-type=primary -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=4 --txq=4 --num-procs=2 --proc-id=1

2. check the ouput of each process::

    process 1 launches successfully
    process 2 launches failed and output contains 'Is another primary process running?'

Test Case: test_multiprocess_negative_exceed_process_num
========================================================
1. start 3 process exceed the specifed num 2::

   ./dpdk-testpmd -l 1,2 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=8 --txq=8 --num-procs=2 --proc-id=0
   ./dpdk-testpmd -l 3,4 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=8 --txq=8 --num-procs=2 --proc-id=1
   ./dpdk-testpmd -l 5,6 --proc-type=auto -a 0000:05:01.0  --log-level=ice,7 -- -i --rxq=8 --txq=8 --num-procs=2 --proc-id=2

2. check the ouput of each process::

    the first and second processes should be launched successfully
    the third process should be launched failed and output should contain the following string:
    'multi-process option proc-id(2) should be less than num-procs(2)'

Test Case: test_multiprocess_negative_action
============================================
Subcase 1: test_secondary_process_port_stop
-------------------------------------------
test steps
~~~~~~~~~~

1. Launch the app ``testpmd``, start 2 process with the following arguments::

   ./dpdk-testpmd -l 1,2 --proc-type=auto -a 0000:17:01.0  --log-level=ice,7 -- -i  --num-procs=2 --proc-id=0
   ./dpdk-testpmd -l 3,4 --proc-type=auto -a 0000:17:01.0  --log-level=ice,7 -- -i  --num-procs=2 --proc-id=1

2. stop port in primary process::

    primary process:
      testpmd> port stop 0

expected result
~~~~~~~~~~~~~~~

   Check that there are no core dump messages in the output.

Subcase 2: test_secondary_process_port_reset
--------------------------------------------
test steps
~~~~~~~~~~

1. Launch the app ``testpmd``, start 2 process with the following arguments::

   ./dpdk-testpmd -l 1,2 --proc-type=auto -a 0000:17:01.0  --log-level=ice,7 -- -i  --num-procs=2 --proc-id=0
   ./dpdk-testpmd -l 3,4 --proc-type=auto -a 0000:17:01.0  --log-level=ice,7 -- -i  --num-procs=2 --proc-id=1

2. reset port in secondary process::

    secondary process:
      testpmd> port stop 0
      testpmd> port reset 0

expected result
~~~~~~~~~~~~~~~

   Check that there are no core dump messages in the output.