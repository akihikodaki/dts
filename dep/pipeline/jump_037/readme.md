Test Case: test_jump_037
------------------------

    Instructions being tested:
        jmpneq LABEL t.field h.field

    Description:
        Drop packets other than with ether type 0x0800. If the ipv4 protocol is tcp, transmit the packet as it is back on the same port.
        Drop all other packets.

    Verification:
        Packets with ether type not equal to 0x0800 should be dropped. If the ipv4 protocol is tcp, the packet should be transmitted as it
        is back on the same port. All other packets should be dropped.
