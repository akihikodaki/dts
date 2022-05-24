.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

=================================================================
Intel® Ethernet 700 Series Configuration of RSS in RTE Flow Tests
=================================================================

Description
===========

The feature remove legacy filter API and switch to rte_flow in driver i40e,
ixgbe, ice. What is need is that remove the function in filter_ctrl ops in
drivers and implement functions in rte_flow. Many functions have been
implemented in rte_flow in the early patches. this feature implement that
set global configurations of hash filters, set symmetric hash configuration
enable and Set GRE key length for input set in driver i40e. 

Prerequisites
=============

1.Bind PF ports to igb_uio driver::

    usertools/dpdk-devbind.py --bind=igb_uio 0000:81:00.0

2.Start testpmd on host::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4  -a 81:00.0 -- -i --txq=8 --rxq=8
    testpmd>set verbose 1
    testpmd>start

Test Case: test symmetric hash configuration
============================================

create a rule that set symmetric hash configuration enable::

    testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end func symmetric_toeplitz queues end / end
    testpmd> flow list 0

verify the Rule is RSS.

send 2 packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.2")/TCP(sport=1024, dport=1025)/Raw(load='X'*1000)],iface='ens802f3')
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.1")/TCP(sport=1025, dport=1024)/Raw(load='X'*1000)],iface='ens802f3')

vefify two packets have the same RSS hash value.

destroy the rule::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

verify the rule has been destroyed.

create a rule that set symmetric hash configuration disable::

    testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end queues end / end
    testpmd> flow list 0

verify the Rule is RSS.

send 2 packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.2")/TCP(sport=1024, dport=1025)/Raw(load='X'*1000)],iface='ens802f3')
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.1")/TCP(sport=1025, dport=1024)/Raw(load='X'*1000)],iface='ens802f3')

vefify two packets have different RSS hash values

Test Case: test set hash input set for ipv4-tcp
===============================================

test all different hash input set for ipv4-tcp
1. Set hash input set for ipv4-tcp l3-src-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())],iface='ens802f3')

   verify the packet have different RSS hash value with above.

2. Set hash input set for ipv4-tcp l3-dst-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst="192.168.0.2")/TCP(sport=RandShort(),dport=RandShort())],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst="192.168.0.2")/TCP(sport=RandShort(),dport=RandShort())],iface='ens802f3')

   verify the packet have different RSS hash value with above.

3. Set hash input set for ipv4-tcp l4-src-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())/TCP(sport=1024,dport=RandShort())],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())/TCP(sport=1024,dport=RandShort())],iface='ens802f3')

   verify the packet have different RSS hash value with above.

4. Set hash input set for ipv4-tcp l4-dst-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())/TCP(sport=RandShort(),dport=1025)],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())/TCP(sport=RandShort(),dport=1025)],iface='ens802f3')

   verify the packet have different RSS hash value with above.

5. Set hash input set for ipv4-tcp l3-src-only and l3-dst-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l3-dst-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=RandShort(),dport=RandShort())],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=RandShort(),dport=RandShort())],iface='ens802f3')

   verify the packet have different RSS hash value with above.

6. Set hash input set for ipv4-tcp l4-src-only and l4-dst-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only l4-dst-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())/TCP(sport=1024,dport=1025)],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.
   
   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())/TCP(sport=1024,dport=1025)],iface='ens802f3')

   verify the packet have different RSS hash value with above.

7.Set hash input set for ipv4-tcp l4-src-only and l3-src-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only l3-src-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst=RandIP())/TCP(sport=1024,dport=RandShort())],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst=RandIP())/TCP(sport=1024,dport=RandShort())],iface='ens802f3')

   verify the packet have different RSS hash value with above.

8. Set hash input set for ipv4-tcp l4-dst-only and l3-dst-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only l3-dst-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst="192.168.0.2")/TCP(sport=RandShort(),dport=1025)],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst="192.168.0.2")/TCP(sport=RandShort(),dport=1025)],iface='ens802f3')

   verify the packet have different RSS hash value with above.

9. Set hash input set for ipv4-tcp l4-src-only and l3-dst-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only l3-dst-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst="192.168.0.2")/TCP(sport=1024,dport=RandShort())],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst="192.168.0.2")/TCP(sport=1024,dport=RandShort())],iface='ens802f3')

   verify the packet have different RSS hash value with above.

10. Set hash input set for ipv4-tcp l4-dst-only and l3-src-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only l3-src-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst=RandIP())/TCP(sport=RandShort(),dport=1025)],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst=RandIP())/TCP(sport=RandShort(),dport=1025)],iface='ens802f3')

   verify the packet have different RSS hash value with above.

11. Set hash input set for ipv4-tcp l4-src-only, l4-dst-only and l3-dst-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only l4-dst-only l3-dst-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst="192.168.0.2")/TCP(sport=1024,dport=1025)],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst="192.168.0.2")/TCP(sport=1024,dport=1025)],iface='ens802f3')

   verify the packet have different RSS hash value with above.

12. Set hash input set for ipv4-tcp l4-src-only, l4-dst-only and l3-src-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only l4-dst-only l3-src-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst=RandIP())/TCP(sport=1024,dport=1025)],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst=RandIP())/TCP(sport=1024,dport=1025)],iface='ens802f3')

   verify the packet have different RSS hash value with above.

13. Set hash input set for ipv4-tcp l4-dst-only, l3-dst-only and l3-src-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only l3-dst-only l3-src-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=RandShort(),dport=1025)],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=RandShort(),dport=1025)],iface='ens802f3')

   verify the packet have different RSS hash value with above.

14. Set hash input set for ipv4-tcp l4-src-only,  l3-src-only and l3-dst-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only l3-dst-only l3-src-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=1024,RandShort())],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=1024,RandShort())],iface='ens802f3')

   verify the packet have different RSS hash value with above.

15. Set hash input set for ipv4-tcp l4-src-only, l4-dst-only, l3-src-only and l3-dst-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only l4-dst-only l3-src-only l3-dst-only end queues end / end

   verify the Rule create successfully.

   send 1 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=1024,dport=1025)],iface='ens802f3')

   verify the RSS hash value valid.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=1024,dport=1025)],iface='ens802f3')

   verify the packet have same RSS hash value as above.

Test Case: test set hash input set for ipv4-udp
================================================

test all different hash input set for ipv4-udp
the same steps as step 1-15 for ipv4-tcp, just replace tcp with udp.

Test Case: test set hash input set for ipv4-sctp
================================================

test all different hash input set for ipv4-sctp
the same steps as step 1-15 for ipv4-tcp, just replace tcp with sctp.

Test Case: test set hash input set for ipv6-tcp
================================================

test all different hash input set for ipv6-tcp
the same steps as step 1-15 for ipv4-tcp, just replace ipv4 with ipv6.

Test Case: test set hash input set for ipv6-udp
================================================

test all different hash input set for ipv6-udp
the same steps as step 1-15 for ipv4-tcp, just replace ipv4-tcp with ipv6-udp.

Test Case: test set hash input set for ipv6-sctp
================================================

test all different hash input set for ipv6-sctp
the same steps as step 1-15 for ipv4-tcp, just replace ipv4-tcp with ipv6-sctp.

Test Case: test set hash input set for ipv4-other
=================================================

test all different hash input set for ipv4-other
1. Set hash input set for ipv4-other l3-src-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other l3-src-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst=RandIP())/GRE(key_present=1,proto=2048,key=67108863)/IP()],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst=RandIP())/GRE(key_present=1,proto=2048,key=67108863)/IP()],iface='ens802f3')

   verify the packet have different RSS hash value with above.

2. Set hash input set for ipv4-other l3-dst-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other l3-dst-only end queues end / end

   verify the Rule create successfully.

   send 10 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst="192.168.0.2")/GRE(key_present=1,proto=2048,key=67108863)/IP()],iface='ens802f3',count=10)

   verify 10 packets have the same RSS hash value.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst="192.168.0.2")/GRE(key_present=1,proto=2048,key=67108863)/IP()],iface='ens802f3')

   verify the packet have different RSS hash value with above.

3. Set hash input set for ipv4-other l3-src-only and l3-dst-only::

        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other l3-src-only l3-dst-only end queues end / end

   verify the Rule create successfully.

   send 1 packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/GRE(key_present=1,proto=2048,key=67108863)/IP()],iface='ens802f3')

   verify the RSS hash value valid.

   destroy the rule and create a new rule with default inputset::

        testpmd> flow destroy 0 rule 0
        testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other end queues end / end

   send 1 packet same as above::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/GRE(key_present=1,proto=2048,key=67108863)/IP()],iface='ens802f3')

   verify the packet have same RSS hash value as above.

Test Case: test set hash input set for ipv6-other
=================================================

test all different hash input set for ipv6-other
the same steps as step 1-3 for ipv4-other, just replace ipv4 with ipv6.

Test Case: test flow validate
=============================

1. validate the rule::

        testpmd> flow validate 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end queues end / end
        testpmd> flow validate 0 ingress pattern end actions rss types end queues 0 1 end / end

   verify the rule validate successfully.

2. validate the rule::

         flow validate 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end queues 0 1 end / end

   verify the rule validate failed.

Test Case: test query RSS rule
==============================

create different RSS rules::

    testpmd> flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end queues end func symmetric_toeplitz / end
    testpmd> flow create 0 ingress pattern end actions rss types end queues end func simple_xor / end
    testpmd> flow create 0 ingress pattern end actions rss types end queues 1 2 end / end
    testpmd> flow list 0

verify the Rules create successfully.

query::

    testpmd> flow query 0 0 rss
    testpmd> flow query 0 1 rss
    testpmd> flow query 0 2 rss
    testpmd> flow query 0 3 rss

verify the function, type and queues information correct.

delete all the rss rules::

    testpmd> flow flush 0

query::

    testpmd> flow query 0 0 rss

verify the testpmd report none rss rule exist.
