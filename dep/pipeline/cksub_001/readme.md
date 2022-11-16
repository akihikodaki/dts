Test Case: test_ckadd_001
-------------------------

    Instructions being tested:
        cksub h.field h.field

    Description:
        For ttl value equal to zero, discard the packet. For ttl greater than zero, decrement tha value by one and update
        its checksum. Transmit the packet back on the same port.

    Verification:
        Packets with zero ttl should be discarded. For others the ttl should be decremented by one and checksum should be
        updated accordingly.

    Input IPv4 Packet Details:
        total length: 20 (ipv4 header) + 20 (tcp header) + 6 (payload) => 46 bytes

    Input packet IPv4 header checksum calculation
        Without checksum: 45 00 00 2e 00 00 00 00 40 06 00 00 64 00 00 0a c8 00 00 0a

        Without checksum: 4500 002e 0000 0000 4006 0000 6400 000a c800 000a

        Sum: 1 b148 => b149
        Checksum: 4eb6

        With checksum: 4500 002e 0000 0000 4006 4eb6 6400 000a c800 000a

    Output packet IPv4 header checksum calculation
        Without checksum: 45 00 00 2e 00 00 00 00 3f 06 00 00 64 00 00 0a c8 00 00 0a

        Without checksum: 4500 002e 0000 0000 3f06 0000 6400 000a c800 000a

        Sum: 1 b048 => b049
        Checksum: 4fb6

        With checksum: 4500 002e 0001 2000 4006 4fb6 6400 000a c800 000a
