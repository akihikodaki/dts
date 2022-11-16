Test Case: test_extract_emit_009
--------------------------------

    Instructions being tested:
        emit h.field

    Description:
        For the received packet, extract its ethernet header and without modifying it, transmit the packet back on the same port.

    Verification:
        The transmitted packet should be same as that of the received packet.
