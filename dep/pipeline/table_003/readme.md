
Test Case: test_table_003
-------------------------

	Description:
		Testing the table update scenarios for wildcard match table type.

	Scenario: Empty Table
		Test: Lookup miss for any packet.
		CMD_FILE: None
		PCAP Files: in_1.txt, out_1.txt

	Scenario: Table with a Single Key
		Test: Lookup hit for the right packet, lookup miss with any other packet.
		CMD_FILE: cmd_2.txt
		PCAP Files: in_2.txt, out_2.txt

	Scenario: Table with 2 Keys
		Test: Lookup hit for the right packets (hitting key A or key B), lookup miss for any other
			  packet. To check whether adding key B does not (incorrectly) override key A in the table.
		CMD_FILE: cmd_3.txt
		PCAP Files: in_3.txt, out_3.txt

	Scenario: Key Deletion
		Test: Table with 2 rules (key A first, key B second), lookup hit for both.
			  Delete key A => lookup MISS for key A (deleted), lookup HIT for key B (still in the table).
			  Delete key B => lookup MISS for both keys A and B (deleted).
		CMD_FILE: cmd_4_1.txt, cmd_4_2.txt
		PCAP Files: in_4_1.txt, out_4_1.txt, in_4_2.txt, out_4_2.txt

	Scenario: Action Update
		Test: Add key A with action X => lookup hit for key A with action X executed.
			  Add the same key A with action Y => lookup hit for key A with action Y being executed at this point.

    Scenario: Default Entry Test
		Empty table => lookup MISS with default action executed.
		Add key A => lookup hit for the right packet with the specific key associated action executed,
					 lookup miss for any other packets with default action executed.
