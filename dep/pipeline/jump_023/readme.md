Test Case: test_jump_023
------------------------

    Instructions being tested:
        jmpeq LABEL m.field m.field

    Description:
        For packets with destination ipv4 address as 0xaa0000bb, transmit them back on the same port. Drop all other packets.

    Verification:
        Packets with destination ipv4 address as 0xaa0000bb should be transmitted as it is back on same port. All other packets should
        be dropped.
