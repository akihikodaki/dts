Test Case: test_mov_005
-----------------------

    Instructions being tested:
        mov m.field t.field

    Description:
	For a packet with matching destination MAC address, Update the output port value from the table entry.

    Verification:
        Packet should be received on the port mentioned in the table.
