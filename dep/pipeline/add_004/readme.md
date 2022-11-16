Test Case: test_add_004
-----------------------

    Instruction being tested:
        add m.field h.field

    Description:
        For the received packet ipv4 dest addr = ethernet src addr + ipv4 dest addr, ethernet src addr = ethernet src addr + ethernet dest addr and, ipv4 src addr = ipv4 header checksum + ipv4 src addr

    Verification:
        Verify using input and output pcap files.
