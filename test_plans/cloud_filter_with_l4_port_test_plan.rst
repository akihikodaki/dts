.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2020 Intel Corporation

===================================
Cloud filter with l4 port test plan
===================================

Prerequisites
=============

1. Hardware:
   Intel® Ethernet 700 Series

2. software:
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. bind the pf to dpdk driver::

    ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:81:00.0

4.Launch the testpmd::
    ./build/app/dpdk-testpmd -l 0-3 -n 4 -a 81:00.0 --file-prefix=test -- -i --rxq=16 --txq=16 --disable-rss
    testpmd> set fwd rxonly
    testpmd> set promisc all off
    testpmd> set verbose 1
    testpmd> start

Test Case 1: ipv4-udp_sport only
================================

    1. validate a source port rule::
        testpmd> flow validate 0 ingress pattern eth / ipv4 / udp src is 156 / end actions pf / queue index 1 / end

        Verify the command can validate::
            Flow rule validated

    2. create a source port rule::
        testpmd> flow create 0 ingress pattern eth / ipv4 / udp src is 156 / end actions pf / queue index 1 / end

        testpmd> flow list 0

        Verify there is one rule.

        send matched packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/UDP(sport=156)/Raw('x' * 80)

        Verify packets will be received in queue 1.

        send no matched packet::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/UDP(sport=111)/Raw('x' * 80)

        Verify packets will not be received in queue 1.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/UDP(sport=156)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 2: ipv4-udp_dport only
================================

    1. validate a destination port rule::
        testpmd> flow validate 0 ingress pattern eth / ipv4 / udp dst is 156 / end actions pf / queue index 1 / end

        Verify the command can validate::
            Flow rule validated

    2. create a destination port rule::
        testpmd> flow create 0 ingress pattern eth / ipv4 / udp dst is 156 / end actions pf / queue index 1 / end

        testpmd> flow list 0

        Verify there is one rule.

        send matched packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/UDP(dport=156)/Raw('x' * 80)

        Verify packets will be received in queue 1.

        send no matched packet::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/UDP(dport=111)/Raw('x' * 80)

        Verify packets will not be received in queue 1.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/UDP(dport=156)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 3: ipv4-tcp_sport only
================================

    1. validate a source port rule::
        testpmd> flow validate 0 ingress pattern eth / ipv4 / tcp src is 156 / end actions pf / queue index 1 / end

        Verify the command can validate::
            Flow rule validated

    2. testpmd> flow create 0 ingress pattern eth / ipv4 / tcp src is 156 / end actions pf / queue index 1 / end

        testpmd> flow list 0

        Verify there is one rule.

        send matched packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/TCP(sport=156)/Raw('x' * 80)

        Verify packets will be received in queue 1.

        send no matched packet::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/TCP(sport=111)/Raw('x' * 80)

        Verify packets will not be received in queue 1.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/TCP(sport=156)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 4: ipv4-tcp_dport only
================================

    1. validate a destination port rule::
        testpmd> flow validate 0 ingress pattern eth / ipv4 / tcp dst is 156 / end actions pf / queue index 1 / end

        Verify the command can validate::
            Flow rule validated

    2. create a destination port rule::
        testpmd> flow create 0 ingress pattern eth / ipv4 / tcp dst is 156 / end actions pf / queue index 1 / end

        testpmd> flow list 0

        Verify there is one rule.

        send matched packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/TCP(dport=156)/Raw('x' * 80)

        Verify packets will be received in queue 1.

        send no matched packet::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/TCP(dport=111)/Raw('x' * 80)

        Verify packets will not be received in queue 1.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/TCP(dport=156)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 5: ipv4-sctp_sport only
=================================

    1. validate a source port rule::
        testpmd> flow validate 0 ingress pattern eth / ipv4 / sctp src is 156 / end actions pf / queue index 1 / end

        Verify the command can validate::
            Flow rule validated

    2. create a source port rule::
        testpmd> flow create 0 ingress pattern eth / ipv4 / sctp src is 156 / end actions pf / queue index 1 / end

        testpmd> flow list 0

        Verify there is one rule.

        send matched packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/SCTP(sport=156)/Raw('x' * 80)

        Verify packets will be received in queue 1.

        send no matched packet::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/SCTP(sport=111)/Raw('x' * 80)

        Verify packets will not be received in queue 1.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/SCTP(sport=156)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 6: ipv4-sctp_dport only
=================================

    1. validate a destination port rule::
        testpmd> flow validate 0 ingress pattern eth / ipv4 / sctp dst is 156 / end actions pf / queue index 1 / end

        Verify the command can validate::
            Flow rule validated

    2. create a destination port rule::
        testpmd> flow create 0 ingress pattern eth / ipv4 / sctp dst is 156 / end actions pf / queue index 1 / end

        testpmd> flow list 0

        Verify there is one rule.

        send matched packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/SCTP(dport=156)/Raw('x' * 80)

        Verify packets will be received in queue 1.

        send no matched packet::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/SCTP(dport=111)/Raw('x' * 80)

        Verify packets will not be received in queue 1.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/SCTP(dport=156)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 7: ipv6-udp_sport only
================================

    1. validate a source port rule::
        testpmd> flow validate 0 ingress pattern eth / ipv6 / udp src is 156 / end actions pf / queue index 1 / end

        Verify the command can validate::
            Flow rule validated

    2. create a source port rule::
        testpmd> flow create 0 ingress pattern eth / ipv6 / udp src is 156 / end actions pf / queue index 1 / end

        testpmd> flow list 0

        Verify there is one rule.

        send matched packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/UDP(sport=156)/Raw('x' * 80)

        Verify packets will be received in queue 1.

        send no matched packet::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/UDP(sport=111)/Raw('x' * 80)

        Verify packets will not be received in queue 1.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/UDP(sport=156)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 8: ipv6-udp_dport only
================================

    1. validate a destination port rule::
        testpmd> flow validate 0 ingress pattern eth / ipv6 / udp dst is 156 / end actions pf / queue index 1 / end

        Verify the command can validate::
            Flow rule validated

    2. create a destination port rule::
        testpmd> flow create 0 ingress pattern eth / ipv6 / udp dst is 156 / end actions pf / queue index 1 / end

        testpmd> flow list 0

        Verify there is one rule.

        send matched packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/UDP(dport=156)/Raw('x' * 80)

        Verify packets will be received in queue 1.

        send no matched packet::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/UDP(dport=111)/Raw('x' * 80)

        Verify packets will not be received in queue 1.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/UDP(dport=156)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 9: ipv6-tcp_sport only
================================

    1. validate a source port rule::
        testpmd> flow validate 0 ingress pattern eth / ipv6 / tcp src is 156 / end actions pf / queue index 1 / end

        Verify the command can validate::
            Flow rule validated

    2. testpmd> flow create 0 ingress pattern eth / ipv6 / tcp src is 156 / end actions pf / queue index 1 / end

        testpmd> flow list 0

        Verify there is one rule.

        send matched packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/TCP(sport=156)/Raw('x' * 80)

        Verify packets will be received in queue 1.

        send no matched packet::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/TCP(sport=111)/Raw('x' * 80)

        Verify packets will not be received in queue 1.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/TCP(sport=156)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 10: ipv6-tcp_dport only
=================================

    1. validate a destination port rule::
        testpmd> flow validate 0 ingress pattern eth / ipv6 / tcp dst is 156 / end actions pf / queue index 1 / end

        Verify the command can validate::
            Flow rule validated

    2. create a destination port rule::
        testpmd> flow create 0 ingress pattern eth / ipv6 / tcp dst is 156 / end actions pf / queue index 1 / end

        testpmd> flow list 0

        Verify there is one rule.

        send matched packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/TCP(dport=156)/Raw('x' * 80)

        Verify packets will be received in queue 1.

        send no matched packet::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/TCP(dport=111)/Raw('x' * 80)

        Verify packets will not be received in queue 1.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/TCP(dport=156)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 11: ipv6-sctp_sport only
==================================

    1. validate a source port rule::
        testpmd> flow validate 0 ingress pattern eth / ipv6 / sctp src is 156 / end actions pf / queue index 1 / end

        Verify the command can validate::
            Flow rule validated

    2. create a source port rule::
        testpmd> flow create 0 ingress pattern eth / ipv6 / sctp src is 156 / end actions pf / queue index 1 / end

        testpmd> flow list 0

        Verify there is one rule.

        send matched packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/SCTP(sport=156)/Raw('x' * 80)

        Verify packets will be received in queue 1.

        send no matched packet::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/SCTP(sport=111)/Raw('x' * 80)

        Verify packets will not be received in queue 1.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/SCTP(sport=156)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 12: ipv6-sctp_dport only
==================================

    1. validate a destination port rule::
        testpmd> flow validate 0 ingress pattern eth / ipv6 / sctp dst is 156 / end actions pf / queue index 1 / end

        Verify the command can validate::
            Flow rule validated

    2. create a destination port rule::
        testpmd> flow create 0 ingress pattern eth / ipv6 / sctp dst is 156 / end actions pf / queue index 1 / end

        testpmd> flow list 0

        Verify there is one rule.

        send matched packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/SCTP(dport=156)/Raw('x' * 80)

        Verify packets will be received in queue 1.

        send no matched packet::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/SCTP(dport=111)/Raw('x' * 80)

        Verify packets will not be received in queue 1.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IPv6()/SCTP(dport=156)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 13: multi-rule
============================================================

    1. create multi-rule with different input set rules::
        creat rules::
            testpmd> flow create 0 ingress pattern eth / ipv4 / udp src is 11 / end actions pf / queue index 1 / end
            testpmd> flow create 0 ingress pattern eth / ipv4 / tcp src is 22 / end actions pf / queue index 2 / end
            testpmd> flow create 0 ingress pattern eth / ipv4 / sctp src is 33 / end actions pf / queue index 3 / end
            testpmd> flow create 0 ingress pattern eth / ipv4 / udp dst is 44 / end actions pf / queue index 4 / end
            testpmd> flow create 0 ingress pattern eth / ipv4 / tcp dst is 55 / end actions pf / queue index 5 / end
            testpmd> flow create 0 ingress pattern eth / ipv4 / sctp dst is 66 / end actions pf / queue index 6 / end

        send packets::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/UDP(sport=11)/Raw('x' * 80)
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/TCP(sport=22)/Raw('x' * 80)
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/SCTP(sport=33)/Raw('x' * 80)
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/UDP(dport=44)/Raw('x' * 80)
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/TCP(dport=55)/Raw('x' * 80)
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/SCTP(dport=66)/Raw('x' * 80)

        Verify each packet can match the right queue.

    2. destroy the rule::
        testpmd> flow destroy 0 rule 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/UDP(sport=11)/Raw('x' * 80)

        packets should be in queue 0.

    3. flush the rule::
        testpmd> flow flush 0

        send packets match rule 0::
            p = Ether(dst="3C:FD:FE:CF:31:D8")/IP()/TCP(sport=22)/Raw('x' * 80)

        packets should be in queue 0.

Test Case 14: NEGATIVE_TEST
====================================

1. rules can not create

    1) unsupported rules::
        create rules::
            testpmd> flow create 0 ingress pattern eth / ipv4 / udp src is 156 dst is 156 / end actions pf / queue index 1 / end

        Verify rules can not create.

    2) conflicted rules::
        create one rule::
            testpmd> flow create 0 ingress pattern eth / ipv4 / udp src is 156 / end actions pf / queue index 1 / end

        create conflicted rules::
            testpmd> flow create 0 ingress pattern eth / ipv4 / udp src is 156 / end actions pf / queue index 2 / end

        Verify rules can not create.
