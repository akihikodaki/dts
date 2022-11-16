
Test Case: test_jump_020
------------------------

    Instructions being tested:
        jmpeq LABEL h.field h.field

    Description:
        For the received packet, if it has matching source MAC address,
        destination ipv4 address and source ipv4 address transmit it as it is
        back on the same port. Drop all other packets.

    Verification:
        Verify using input and output pcap files.
