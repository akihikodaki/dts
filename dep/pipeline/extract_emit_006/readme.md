Test Case: test_extract_emit_006
--------------------------------
    Instructions being tested:
        extract h.field (level 6)
        emit h.field (level 6)

    Description:
        For the received packet, extract its outer ethernet, outer ipv4, outer udp, outer vxlan, ethernet and ipv4 headers and without modifying them, transmit the packet back on the same port.

    Verification:
        The transmitted packet should be same as that of the received packet.
