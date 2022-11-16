Test Case: test_extract_emit_007
--------------------------------
    Instructions being tested:
        extract h.field (level 7)
        emit h.field (level 7)

    Description:
        For the received packet, extract its outer ethernet, outer ipv4, outer udp, outer vxlan, ethernet, ipv4 and tcp headers and without modifying them,
        transmit the packet back on the same port.

    Verification:
        The transmitted packet should be same as that of the received packet.
