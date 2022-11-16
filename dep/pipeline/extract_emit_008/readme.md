Test Case: test_extract_emit_008
--------------------------------
    Instructions being tested:
        extract h.field (level 8)
        emit h.field (level 8)

    Description:
        For the received packet, extract its outer ethernet, outer ipv4, outer udp, outer vxlan, ethernet, vlan, ipv4 and tcp headers and without modifying
        them, transmit the packet back on the same port.

    Verification:
        The transmitted packet should be same as that of the received packet.
