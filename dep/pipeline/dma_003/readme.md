
Test Case: test_dma_003
-----------------------

    Instructions being tested:
        mov h.header.field t.field (level 3)
        validate h.header (level 3)

    Description:
        Based on the destination MAC address of the received packet ethernet,
        ipv4 and tcp headers are updated from the table.

    Verification:
        Transmitted packet should have the ethernet, ipv4 and tcp headers as
        defined in the table.
