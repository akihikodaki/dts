Test Case: test_extract_emit_003
--------------------------------
    Instructions being tested:
        extract h.field (level 3)
        emit h.field (level 3)

    Description:
        For the received packet, extract its ethernet, ipv4 and tcp header and without modifying it, transmit the packet back on the same port.

    Verification:
        The transmitted packet should be same as that of the received packet.
