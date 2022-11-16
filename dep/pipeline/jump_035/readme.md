Test Case: test_jump_035
------------------------

    Instructions being tested:
        jmpneq LABEL m.field m.field

    Description:
        Drop all the packets with destination ipv4 address equal to 0xaa0000bb. Transmit all others back on the same port.

    Verification:
        Packets with destination ipv4 address equal to 0xaa0000bb should be dropped and others should be transmitted as it is back on
        the same port.
