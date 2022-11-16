Test Case: test_shl_003
-------------------------

    Instructions being tested:
        shl h.field m.field

    Description:
        For the received packet, ip head checksum = ip header checksum << ip protocol value, ip ttl = ip ttl << ip protocol value , and ip src addr = ip src addr << ethernet dst addr

    Verification:
        Verify using input and output pcap files.
