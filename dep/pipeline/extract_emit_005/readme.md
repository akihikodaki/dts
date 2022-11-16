Test Case: test_extract_emit_005
--------------------------------
    Instructions being tested:
        extract h.field (level 5)
        emit h.field (level 5)

    Description:
        For the received packet, extract its ethernet, vlan 1, vlan 2, ipv4 and tcp header and without modifying it, transmit the packet back on the same port.

    Verification:
        The transmitted packet should be same as that of the received packet.
