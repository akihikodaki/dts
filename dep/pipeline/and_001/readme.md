
Test Case: test_and_001
-----------------------

    Instruction being tested:
        and h.field h.field

    Description:
        For the received packet, bitwise AND the bits of destination IP address
        and source MAC address, source MAC address and destination MAC address,
        destination MAC address and source IP address and transmit the packet
        back on the same port.

    Verification:
        Verify using input and output pcap files.
