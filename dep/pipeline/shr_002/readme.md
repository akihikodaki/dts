Test Case: test_shr_002
-----------------------

    Instructions being tested:
        shr m.field h.field

    Description:
        For the received packet, ethernet src addr = ethernet src addr >> ipv4 protocol, ipv4 ttl = ipv4 ttl >> ipv4 protocol , and ipv4 src addr = ipv4 src addr >> ethernet dst addr

    Verification:
        Verify using input and output pcap files.
