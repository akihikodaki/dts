
Test Case: test_jump_032
------------------------

    Instructions being tested:
        jmpneq LABEL h.field h.field

    Description:
        For the received packet, if its source MAC address, destination IP
        address and source IP address are different, transmit it as it is back
        on the same port. Drop all other packets.

    Verification:
        Verify using input and output pcap files.
