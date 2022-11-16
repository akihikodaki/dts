Test Case: test_sub_004
-----------------------

    Instruction being tested:
        sub m.field h.field

    Description:
        For the received packet, ethernet src addr = ethernet src addr - ipv4 dst addr, ipv4 src addr = ipv4 src addr - ipv4 dst addr ,and ipv4 ttl = ipv4 ttl - ipv4 dst addr

    Verification:
        Verify using input and output pcap files.
