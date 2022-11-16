
Test Case: test_dma_002
-----------------------

    Instructions being tested:
        mov h.header.field t.field (level 2)
        validate h.header (level 2)

    Description:
        Based on the destination MAC address of the received packet, ethernet
        and ipv4 headers are updated from the table.

    Verification:
        Transmitted packet should have the ethernet and ipv4 headers as defined
        in the table.
