Test Case: test_sub_006
-----------------------

    Instruction being tested:
        sub m.field m.field

    Description:
        For the received packet, subtract the source MAC address from the destination MAC address and transmit it back on the same port.

    Verification:
        Destination MAC address of the transmitted packet should be the difference of destination and source MAC addresses respectively
        of the received packet.
