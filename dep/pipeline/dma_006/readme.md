
Test Case: test_dma_006
-----------------------

    Instructions being tested:
        mov h.header.field t.field (level 6)
        validate h.header (level 6)

    Description:
        Based on the destination MAC address of the received packet outer
        ethernet, outer ipv4, outer udp, outer vxlan, ethernet and ipv4 headers
        are updated from the table.

    Verification:
        Transmitted packet should have the outer ethernet, outer ipv4, outer
        udp, outer vxlan, ethernet and ipv4 headers as defined in the table.
