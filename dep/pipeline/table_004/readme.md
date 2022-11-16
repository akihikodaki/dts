
Test Case: test_table_004
-------------------------

	Scenario:
		Table with both exact and wildcard match table types present together.

	Description:
		Lookup HIT for the packets matching the key(s) configured in table and associated action to
		be executed. Lookup MISS for packets not matching with any of the keys configured in the
		table and default action to be executed for them.

	Verification:
		Behavior should be as per the description.
