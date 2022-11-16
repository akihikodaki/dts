Test Case: test_or_006
-----------------------

    Instruction being tested:
        or h.field immediate_value

    Description:
        For the received packet, bitwise OR the bits of source and destination IP addresses with 0xF0F0F0F0 and transmit the packet back on the same
        port.

    Verification:
        Bits of source and destination IP addresses of the transmitted packet should be the result of bitwise OR of 0xF0F0F0F0 with that of source
        and destination IP addresses of the received packet.
