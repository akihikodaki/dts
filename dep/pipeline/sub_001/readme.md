Test Case: test_sub_001
-----------------------

    Instruction being tested:
        sub h.field immediate_value

    Description:
        Subtract one from the destination MAC address of the received packet and transmit it back on the same port.

    Verification:
        Destination MAC address of the transmitted packet should be one less than the destination MAC address of the received packet.
