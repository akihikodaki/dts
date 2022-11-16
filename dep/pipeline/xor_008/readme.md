
Test Case: test_xor_008
-----------------------

    Instruction being tested:
        xor h.field m.field

    Description:
        For the received packet, bitwise xor the bits of source and destination
        IP addresses and store the result in destination IP address field and
        transmit the packet back on the same port.

    Verification:
        Bits of destination IP address of the transmitted packet should be the
        result of bitwise xor of source and destination IP addresses of the
        received packet.
