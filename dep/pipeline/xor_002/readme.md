Test Case: test_xor_002
-----------------------

    Instruction being tested:
        xor h.field immediate_value

    Description:
        For the received packet, toggle the bits of source and destination IP address and transmit it back on the same port.

    Verification:
        Bits of source and destination IP addresses of the transmitted packet should be the toggled with respect to the source and destination IP
        addresses respectively of the received packet.
