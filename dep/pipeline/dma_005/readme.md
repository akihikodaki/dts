
Test Case: test_dma_005
-----------------------

    Instructions being tested:
        mov h.header.field t.field (level 5)
        validate h.header (level 5)

    Description:
        Based on the destination MAC address of the received packet ethernet,
        vlan 1, vlan 2, ipv4 and tcp headers are updated from the table.

    Verification:
        Transmitted packet should have the ethernet, vlan 1, vlan 2, ipv4 and
        tcp headers as defined in the table.
