
Test Case: test_dma_004
-----------------------

    Instructions being tested:
        mov h.header.field t.field (level 4)
        validate h.header (level 4)

    Description:
        Based on the destination MAC address of the received packet ethernet,
        vlan, ipv4 and tcp headers are updated from the table.

    Verification:
        Transmitted packet should have the ethernet, vlan, ipv4 and tcp headers
        as defined in the table.
