Test Case: test_jump_029
------------------------

    Instructions being tested:
        jmpeq LABEL h.field immediate_value

    Description:
        For packets with ether type as 0x0800, transmit them back on the same port. Drop all other packets.

    Verification:
        Packets with ether type as 0x0800 should be transmitted as it is back on same port. All other packets should be dropped.
