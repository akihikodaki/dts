
Test Case: test_jump_024
------------------------

    Instructions being tested:
        jmpeq LABEL h.field t.field

    Description:
        Drop packets with ether type other than 0x800. For packets with ipv4
        ether type 0x800, decrement ttl by one. Drop packets with ttl equal to
        0x1.

    Verification:
        Packets with ether type not equal to 0x800 should be dropped. For other
        packets, ttl should be decremented by one. Packets with ttl value of
        0x1 should be dropped.
