
Test Case: test_dma_001
-----------------------

    Instructions being tested:
        dma h.header.field t.field (level 1)
		validate h.header (level 1)

    Description:
		Based on the destination MAC address of the received packet, ethernet
		header is updated from the table.

    Verification:
		Transmitted packet should have the ethernet header as defined in the
		table.
