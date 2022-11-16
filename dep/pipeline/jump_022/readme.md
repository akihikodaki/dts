
Test Case: test_jump_022
------------------------

    Instructions being tested:
        jmpeq LABEL m.field h.field

    Description:
        For the received packet, if the destination IPv4 address is equal to a
        predefined value in metadata, transmit it as it is back on the same
        port. Drop all other packets.

    Verification:
        Verify using input and output pcap files.
