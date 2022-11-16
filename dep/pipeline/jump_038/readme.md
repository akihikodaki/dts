Test Case: test_jump_038
------------------------

    Instructions being tested:
        jmpneq LABEL m.field t.field

    Description:
        Drop packets other than with ether type 0x0800. For packets with ipv4 ether type, decrement ttl by one. Drop packets with
        ttl equal to zero.

    Verification:
        Packets with ether type not equal to 0x0800 should be dropped. For other packets, ttl should be decremented by one. Packets
        with zero ttl should be dropped.
