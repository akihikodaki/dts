
Test Case: test_jump_034
------------------------

    Instructions being tested:
        jmpneq LABEL m.field h.field

    Description:
        For the received packet, if the source & destination IPv4 address are
        not equal to a predefined value in metadata, transmit it as it is back
        on the same port. Drop all other packets.

    Verification:
        Verify using input and output pcap files.
