.. Copyright (c) <2020>, Intel Corporation
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

=============================
Pipeline Tests
=============================

Description
===========
The "examples/pipeline" application is the main DPDK Packet Framework
application.

Prerequisites
==============
The DUT must have four 10G Ethernet ports connected to four ports on
Tester that are controlled by the Scapy packet generator::

    dut_port_0 <---> tester_port_0
    dut_port_1 <---> tester_port_1
    dut_port_2 <---> tester_port_2
    dut_port_3 <---> tester_port_3

Assume four DUT 10G Ethernet ports' pci device id is as the following::

    dut_port_0 : "0000:00:04.0"
    dut_port_1 : "0000:00:05.0"
    dut_port_2 : "0000:00:06.0"
    dut_port_3 : "0000:00:07.0"

Bind them to dpdk igb_uio driver::

    ./usertools/dpdk-devbind.py -b igb_uio 0000:00:04.0 0000:00:05.0 0000:00:06.0 0000:00:07.0

Supporting Files
================
All the supporting files for this test suite are maintained in a tar file named "pipeline.tar.gz"
present in the {DTS_SRC_DIR}/dep directory.

Directory Structure of Each Test Case
=====================================
Within {DTS_SRC_DIR}/dep/pipeline.tar.gz, all files related to a particular test case are maintained
in a separate directory of which the directory structure is shown below::

    test_case_name [directory]
        test_case_name.spec
        test_case_name.cli
        table.txt [applicable for test cases requiring it]
        readme.txt
        pcap_files [subdirectory]
            in_x.txt [x: 1-4; depending on test case]
            out_x.txt [x: 1-4; depending on test case]

For an example, files related to mov_001 test case are maintained as shown below::

    mov_001 [directory]
        mov_001.spec
        mov_001.cli
        readme.txt
        pcap_files [subdirectory]
            in_1.txt
            out_1.txt

Template of each Test Case
===========================
1. Edit test_case_name/test_case_name.cli:
   change pci device id of LINK0, LINK1, LINK2, LINK3 to pci device id of
   dut_port_0, dut_port_1, dut_port_2, dut_port_3

2. Run pipeline app as the following::

    x86_64-native-linuxapp-gcc/examples/dpdk-pipeline  -c 0x3 -n 4 -- -s /tmp/pipeline/test_case_name/test_case_name.cli

3. Send packets at tester side using scapy. The packets to be sent are maintained in pipeline/test_case_name/pcap_files/in_x.txt

4. Verify the packets received using tcpdump. The expected packets are maintained in pipeline/test_case_name/pcap_files/out_x.txt

5. Test case is considered as successful if the received packets and the expected packets match for all the port combinations used.

Example Test Case: test_mov_001
=========================================
1. Edit mov_001/mov_001.cli:
   change pci device id of LINK0, LINK1, LINK2, LINK3 to pci device id of
   dut_port_0, dut_port_1, dut_port_2, dut_port_3

2. Run pipeline app as the following::

    x86_64-native-linuxapp-gcc/examples/dpdk-pipeline  -c 0x3 -n 4 -- -s /tmp/pipeline/mov_001/mov_001.cli

3. Send packets at tester side using scapy. The packets to be sent are maintained in pipeline/mov_001/pcap_files/in_1.txt

4. Verify the packets received using tcpdump. The expected packets are maintained in pipeline/mov_001/pcap_files/out_1.txt

5. test_mov_001 is considered as successful if the received packets and the expected packets match for all 4 port combinations used.
