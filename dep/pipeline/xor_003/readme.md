Test Case: test_xor_003
-----------------------

    Instruction being tested:
        xor m.field m.field

    Description:
        For the received packet, bitwise xor the bits of source and destination MAC addresses and store the result in destination MAC address
        field and transmit the packet back on the same port.

    Verification:
        Bits of destination MAC address of the transmitted packet should the result of bitwise xor of source and destination MAC addresses
        of the received packet.
