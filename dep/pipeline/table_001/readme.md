Test Case: test_table_001
-------------------------

    Instruction being tested:
        table TABLE_NAME
        return

    Description:
        Copy the destination MAC address of the received packet into the source MAC address and transmit the packet back on the same port.

    Verification:
        Source and destination MAC address fields of transmitted packets by DUT should have same value.
