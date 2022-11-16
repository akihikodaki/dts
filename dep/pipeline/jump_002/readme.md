Test Case: test_jump_002
------------------------

    Instructions being tested:
        jmpv LABEL h.header

    Description:
        For the received packet, if its ether type is 0x0800 transmit it as it is back on the same port else drop the packet.

    Verification:
        All the packets with ether type as 0x0800 should be transmitted back. All others should be dropped.
