Test Case: test_mov_003
-----------------------

    Instruction being tested:
        mov m.field m.field

    Description:
        Copy the destination IP address of the received packet into the source IP address and transmit the packet back on the same port.

    Verification:
        Source and destination IP address fields of transmitted packets should have same value.
