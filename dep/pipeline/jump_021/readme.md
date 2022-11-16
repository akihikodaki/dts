
Test Case: test_jump_021
------------------------

    Instructions being tested:
        jmpeq LABEL h.field m.field

    Description:
        For the received packet, if its ether type is equal to 0x800, transmit
        it as it is back on the same port. Drop all other packets.

    Verification:
        Packets with ether type as 0x800 should be transmitted as it is back on
        the same port. All other packets should be dropped.
