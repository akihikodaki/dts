.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

===========
softnic PMD
===========

Description
===========
The SoftNIC allows building custom NIC pipelines in SW. The Soft NIC pipeline
is configurable through firmware (DPDK Packet Framework script).

Prerequisites
=============
The DUT must have atleast one 10G Ethernet ports connected to one port on
Tester.::

    dut_port_0 <---> tester_port_0

Assume DUT 10G Ethernet ports' pci device id is as the following::

    dut_port_0 : "0000:af:00.1"

Bind them to dpdk vfio-pci driver::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:af:00.1

Supporting Files
================
All the supporting files for this test suite are maintained inside softnic folder, and softnic folder
is present in the {DTS_SRC_DIR}/dep directory.

Directory Structure of Each Test Case
=====================================
Within {DTS_SRC_DIR}/dep/softnic, all files related to a particular test case are maintained
in a separate directory of which the directory structure is shown below::

    test_case_name [directory]
        test_case_name.spec
        test_case_name_x.io [x: 1 to n; depending on the test case]
        test_case_name.cli
        table.txt [applicable for test cases requiring it]
        readme.txt
        pcap_files [subdirectory]
            in.txt
            out.txt

For an example, files related to rx_tx test case are maintained as shown below::

    rx_tx [directory]
        rx_tx.spec
        rx_tx_1.io
        rx_tx_2.io
        rx_tx.cli
        readme.txt
        pcap_files [subdirectory]
            in.txt
            out.txt

Template of each Test Case
===========================
1. Edit test_case_name/test_case_name.io:
   change pci device id of port in and port out to pci device id of dut_port_0

2. Run softnic driver as the following::

    x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 0-2 -n 4  --file-prefix=dpdk_2374972_20221107140937   -s 0x4 -a 0000:af:00.1 \
    --vdev 'net_softnic0,firmware=/tmp/softnic/rx_tx/firmware.cli,cpu_id=1,conn_port=8086' -- -i --portmask=0x2
    testpmd> start

3. Send packets at tester side using scapy. The packets to be sent are maintained in softnic/test_case_name/pcap_files/in.txt

4. Verify the packets received using tcpdump. The expected packets are maintained in softnic/test_case_name/pcap_files/out.txt

5. Test case is considered as successful if the received packets and the expected packets match for all the port combinations used.

Example Test Case : rx_tx
================================
1. Edit rx_tx/rx_tx_1.io:
   change pci device id of port in to pci device id of dut_port_0
   Edit rx_tx/rx_tx_2.io:
   change pci device id of port out to pci device id of dut_port_0

2. Start softnic::

    x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 0-2 -n 4  --file-prefix=dpdk_2374972_20221107140937 \
    -s 0x4 -a 0000:af:00.1 --vdev 'net_softnic0,firmware=/tmp/softnic/rx_tx/firmware.cli,cpu_id=1, \
    conn_port=8086' -- -i --portmask=0x2
    testpmd> start

3. Send packets at tester side using scapy. The packets to be sent are maintained in softnic/rx_tx/pcap_files/in.txt

4. Verify the packets received using tcpdump. The expected packets are maintained in softnic/rx_tx/pcap_files/out.txt

5. Test rx_tx is considered as successful if the received packets and the expected packets match for all port combinations used.