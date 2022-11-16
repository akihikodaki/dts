
Test Case: test_jump_036
------------------------

    Instructions being tested:
        jmpneq LABEL h.field t.field

    Description:
        Drop packets other than with ether type 0x800. For packets with ipv4
        ether type, decrement ttl by one. Drop packets with ttl value equal to
        0x1.

    Verification:
        Packets with ether type not equal to 0x800 should be dropped. For other
        packets, ttl should be decremented by one. Packets with ttl value equal
        to 0x1 should be dropped.
