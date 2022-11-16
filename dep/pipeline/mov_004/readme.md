
Test Case: test_mov_004
-----------------------

    Instructions being tested:
	    mov h.field t.field

    Description:
        For a packet with matching destination MAC address, update the source
        IP address of packet with the IP address of configured rule in the table.

    Verification
        IP address of the output packet should match the IP address of configured
        rule in the table.
