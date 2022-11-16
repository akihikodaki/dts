Test Case: test_sub_003
-----------------------

    Instruction being tested:
        sub m.field immediate_value

    Description:
        Decrement by one the destination MAC address of the received packet by copying that field into metadata and transmit it back on
        the same port.

    Verification:
        Destination MAC address of the transmitted packet should be the one less than that of the received packet.
