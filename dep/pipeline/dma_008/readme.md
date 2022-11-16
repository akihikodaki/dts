
Test Case: test_dma_008
-----------------------

    Instructions being tested:
        dma h.header.field t.field (level 8)
        validate h.header (level 8)

    Description:
        Based on the destination MAC address of the received packet outer
        ethernet, outer ipv4, outer udp, outer vxlan, ethernet, vlan, ipv4 and
        tcp headers are updated from the table.

    Verification:
        Transmitted packet should have the outer ethernet, outer ipv4, outer
        udp, outer vxlan, ethernet, vlan, ipv4 and tcp headers as defined in
        the table.
