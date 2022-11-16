Test Case: test_ckadd_010
-------------------------

    Instructions being tested:
        ckadd h.field h.hdr (h.hdr size not multiple of 20)

    Description:
        Send a packet with zero value in the ipv4 checksum field. For the received packet, calculate the ipv4 checksum
        and update its checksum field with that value and transmit the packet back on the same port.

    Verification:
        For a packet received with zero value in its checksum field, its checksum field should be populated with the
        calculated checksum value.

    Input IPv4 Packet Details:
        total length: 20 (ipv4 header) + 20 (tcp header) + 6 (payload) => 46 bytes

    Input packet 1 IPv4 header checksum calculation
        Without checksum: 45 00 00 2e 00 00 00 00 40 06 00 00 64 00 00 0a c8 00 00 0a dd dd dd dd

        Without checksum: 4500 002e 0000 0000 4006 0000 6400 000a c800 000a dddd dddd

        Sum: 3 6d02 => 6d05
        Checksum: 92fa

        With checksum: 4500 002e 0000 0000 4006 92fa 6400 000a c800 000a dddd dddd

    Input packet 2 IPv4 header checksum calculation (if odd number of bytes are required to be checked at a later stage)
        Without checksum: 45 00 00 2e 00 00 00 00 40 06 00 00 64 00 00 0a c8 00 00 0a dd dd dd

        Without checksum: 4500 002e 0000 0000 4006 0000 6400 000a c800 000a dddd dd

        Sum: 2 9002 => 9004
        Checksum: 6ffb

        With checksum: 4500 002e 0000 0000 4006 92fa 6400 000a c800 000a dddd dddd
