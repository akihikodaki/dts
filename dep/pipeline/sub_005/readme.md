Test Case: test_sub_005
-----------------------

    Instruction being tested:
        sub h.field m.field

    Description:
        For the received packet, ethernet src addr = ethernet src addr - ipv4 total length, ipv4 src addr = ipv4 src addr - ipv4 dst addr , and ipv4 ttl = ipv4 ttl - ipv4 header checksum

    Verification:
		Verify using input and output pcap files.
