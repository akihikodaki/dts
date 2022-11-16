
Test Case: test_dma_007
-----------------------

    Instructions being tested:
        mov h.header.field t.field (level 7)
        validate h.header (level 7)

    Description:
        Based on the destination MAC address of the received packet outer
        ethernet, outer ipv4, outer udp, outer vxlan, ethernet, ipv4 and tcp
        headers are updated from the table.

    Verification:
        Transmitted packet should have the outer ethernet, outer ipv4, outer
        udp, outer vxlan, ethernet, ipv4 and tcp headers as defined in the
        table.
