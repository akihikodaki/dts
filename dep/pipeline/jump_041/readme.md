Test Case: test_jump_041
------------------------

    Instructions being tested:
        jmpneq LABEL h.field immediate_value

    Description:
        Drop all the packets with ether type not equal to 0x0800. Transmit all others back on the same port.

    Verification:
        Packets with ether type not equal to 0x0800 should be dropped and others should be transmitted as it is back on the
        same port.
