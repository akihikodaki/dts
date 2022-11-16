
Test Case: test_jump_033
------------------------

    Instructions being tested:
        jmpneq LABEL h.field m.field

    Description:
        For a received packet, if its source and destination IP addresses are
        not equal to a fixed value, transmit the packet back on the same port.
        Drop all other packets.

    Verification:
        Verify using input and output pcap files.
