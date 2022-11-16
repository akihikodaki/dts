Test Case: test_or_003
-----------------------

    Instruction being tested:
        or m.field m.field

    Description:
        For the received packet, bitwise OR the bits of source and destination MAC addresses and store the result in destination MAC address
        field and transmit the packet back on the same port.

    Verification:
        Bits of destination MAC address of the transmitted packet should be the result of bitwise OR of source and destination MAC addresses
        of the received packet.
