Test Case: test_extract_emit_002
--------------------------------
    Instructions being tested:
        extract h.field (level 2)
        emit h.field (level 2)

    Description:
        For the received packet, extract its ethernet and ipv4 header and without modifying it, transmit the packet back on the same port.

    Verification:
        The transmitted packet should be same as that of the received packet.
