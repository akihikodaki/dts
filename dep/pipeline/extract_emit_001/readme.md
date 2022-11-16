Test Case: test_extract_emit_001
--------------------------------
    Instructions being tested:
        extract h.field
        emit h.field

    Description:
        For the received packet, extract its ethernet header and without modifying it, transmit the packet back on the same port.

    Verification:
        The transmitted packet should be same as that of the received packet.
