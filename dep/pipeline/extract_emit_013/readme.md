Test Case: test_extract_emit_013
--------------------------------
    Instructions being tested:
        extract h.field
		invalidate h (removing one header among 11 headers)
        emit h.field

    Description:
        For the received packet, Invalidate a header among the optimised many emit instructions, transmit the packet back on the same port.

    Verification:
        The received packet should have only valid headers.
