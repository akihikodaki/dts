Test Case: test_add_008
-----------------------

    Instructions being tested:
	add m.field t.field

   Description:
	For a packet with matching destination MAC address, source MAC address is added with the entry in table and updated source MAC address is tranmitted on the same port.

   Verification:
	Packet will be received on the same port and ethernet MAC src address will be the sum of original src MAC address and entry stored in the table.
