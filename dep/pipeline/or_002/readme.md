
Test Case: test_or_002
-----------------------

    Instruction being tested:
        or h.field h.field

    Description:
        For the received packet, bitwise OR the bits of destination IP address
        and source MAC address, source MAC address and destination MAC address,
        destination MAC address and source IP address and transmit the packet
        back on the same port.

    Verification:
        Bits of destination MAC address of the transmitted packet should be the
        result of bitwise OR of source and destination MAC addresses of the
        received packet.
