.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

==========================
ICE DCF DISABLE ACL engine
==========================

Description
===========

Support disabling DCF ACL engine via `devarg` "acl=off" in cmdline, aiming to shorten the DCF startup time.
After disabling the ACL engine, some of the rules supported by the ACL engine will be created by the Switch engine and others will failed to be created,
as shown in the following table.

+-----------+-------------------------------------------------------------------------+---------+---------+
| Pattern   | Input Set                                                               | ACL     | Switch  |
+===========+=========================================================================+=========+=========+
| IPv4      | [Source MAC]                                                            | success | fail    |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Dest MAC]                                                              | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Source IP]                                                             | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Dest IP]                                                               | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Source IP],[Dest IP]                                                   | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Source MAC],[Dest MAC],[Source IP],[Dest IP]                           | success | fail    |
+-----------+-------------------------------------------------------------------------+---------+---------+
| IPv4_TCP  | [Source MAC]                                                            | success | fail    |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Dest MAC]                                                              | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Source IP]                                                             | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Dest IP]                                                               | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Source port]                                                           | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Dest port]                                                             | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Source IP],[Dest IP],[Source port],[Dest port]                         | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Source MAC],[Dest MAC],[Source IP],[Dest IP],[Source port],[Dest port] | success | fail    |
+-----------+-------------------------------------------------------------------------+---------+---------+
| IPv4_UDP  | [Source MAC]                                                            | success | fail    |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Dest MAC]                                                              | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Source IP]                                                             | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Dest IP]                                                               | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Source port]                                                           | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Dest port]                                                             | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Source IP],[Dest IP],[Source port],[Dest port]                         | success | success |
+-----------+-------------------------------------------------------------------------+---------+---------+
|           | [Source MAC],[Dest MAC],[Source IP],[Dest IP],[Source port],[Dest port] | success | fail    |
+-----------+-------------------------------------------------------------------------+---------+---------+
| IPv4_SCTP | all input sets                                                          | success | fail    |
+-----------+-------------------------------------------------------------------------+---------+---------+


Prerequisites
=============

Topology
--------

    dut_port_0 <---> tester_port_0

    dut_port_1 <---> tester_port_1

Hardware
--------

    Supported NICs: columbiaville_25g/columbiaville_100g

Software
--------

    dpdk: http://dpdk.org/git/dpdk

    scapy: http://www.secdev.org/projects/scapy/

General set up
--------------

1. Compile DPDK::

    CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc

2. Get the pci device id of DUT, for example::

    ./usertools/dpdk-devbind.py -s

    0000:17:00.0 'Ethernet Controller E810-C for QSFP 1592' if=ens9 drv=ice unused=vfio-pci

3. Generate 2 VFs on PF0::

    echo 2 > /sys/bus/pci/devices/0000:17:00.0/sriov_numvfs

    ./usertools/dpdk-devbind.py -s
    0000:17:01.0 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf
    0000:17:01.1 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf

4. Set VF0 as trust and set VF1 mac address::

    ip link set ens9 vf 0 trust on
    ip link set ens9 vf 1 mac 00:01:23:45:67:89

5. Bind VFs to dpdk driver::

    modprobe vfio-pci
    ./usertools/dpdk-devbind.py -b=vfio-pci 0000:17:01.0 0000:17:01.1

6. Launch testpmd on VF0, VF0 request DCF mode and add parameter "acl=off" to disable the ACL engine::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:17:01.0,cap=dcf,acl=off -a 0000:17:01.1 --log-level="ice,7" -- -i

    Notice that when launching testpmd, the application prints "ice_flow_init():Engine 4 disabled"

    Quit testpmd::

    testpmd> quit

    Check that when quitting testpmd, the application prints "ice_flow_uninit():Engine 4 disabled skip it"

Test Case
=========

Test Case 1:  Compare startup time
-----------------------------------

It takes too much time to enable the ACL engine when launching testpmd, so the startup time should be shortened after disabling ACL.

test steps
~~~~~~~~~~

1. Disable ACL, execute command and record the time "start_time_disable_acl"::

    echo quit | time ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:17:01.0,cap=dcf,acl=off -a 0000:17:01.1 --log-level="ice,7" -- -i

2. Enable ACL, execute command and record the time "start_time_enable_acl"::

    echo quit | time ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:17:01.0,cap=dcf -a 0000:17:01.1 --log-level="ice,7" -- -i

3. Repeat step 1~2 for at least 6 times to get the average time of "start_time_disable_acl" and "start_time_enable_acl".


expected result
~~~~~~~~~~~~~~~

    Check that the average startup time with "acl=off" is shorter than that without "acl=off".

Test Case 2: disable ACL engine
-------------------------------

Add "--log-level='ice,7'" when launching testpmd, it will print the detailed information when creating one rule.
"Succeeded to create (4) flow" means the rule was created by the ACL engine, "Succeeded to create (2) flow" means it was created by the Switch engine.
Therefore, when creating ACL rules after disabling the ACL engine, the ACL engine will fail to create any of these rules,
but some of them can be successfully created by the switch engine.

test steps
~~~~~~~~~~

1. Launch testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:17:01.0,cap=dcf,acl=off -a 0000:17:01.1 --log-level="ice,7" -- -i

2. Create ACL rules on port 0::

    Switch supported rules::

    ipv4:
        flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:ff / ipv4 / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.0 / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / end actions drop / end
    ipv4_tcp:
        flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:00 / ipv4 / tcp / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / tcp / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.243 / tcp / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 / tcp dst spec 8010 dst mask 65520 / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / tcp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end
    ipv4_udp:
        flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:00 / ipv4 / udp / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / udp / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.243 / udp / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 / udp src spec 8010 src mask 65520 / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 / udp dst spec 8010 dst mask 65520 / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / udp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end

    Switch not supported rules::

    ipv4:
        flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask 00:ff:ff:ff:ff:ff / ipv4 / end actions drop / end
        flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 33:00:00:00:00:02 dst mask ff:ff:ff:ff:ff:fe / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / end actions drop / end
    ipv4_tcp:
        flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:fe / ipv4 / tcp / end actions drop / end
        flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 00:01:23:45:67:89 dst mask ff:ff:ff:ff:00:ff / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / tcp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end
    ipv4_udp:
        flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:fe / ipv4 / udp / end actions drop / end
        flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 00:01:23:45:67:89 dst mask ff:ff:ff:ff:00:ff / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / udp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end
    ipv4_sctp:
        flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:fe / ipv4 / sctp / end actions drop / end
        flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:00 / ipv4 / sctp / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / sctp / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.243 / sctp / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 / sctp src spec 8010 src mask 65520 / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 / sctp dst spec 8010 dst mask 65520 / end actions drop / end
        flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / sctp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end
        flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 00:01:23:45:67:89 dst mask ff:ff:ff:ff:00:ff / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / sctp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end

expected result
~~~~~~~~~~~~~~~

    Check that Switch support rules will be created::

        ice_flow_create(): Succeeded to create (2) flow

    Switch not support rules will be created failed::

        ice_flow_create(): Failed to create flow
        port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7ffd63133730,Invalid input set: Invalid argument

    Both outputs mean that the ACL engine has been disabled.
