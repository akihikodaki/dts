Test Case: test_mov_012
-----------------------

	Instructions being tested:
		mov (h/m).field (h/m).field

	Scenario being tested:
		Mov instruction with custom width destination as well as
		custom width source operands.
		mov dst src
		dst : 32, 48, 96 bit header field
		src : 128 bit header or metadata

	Description:
		The testcase moves ipv6 destination address to the ipv4
		source address and ipv6 source address to the ipv4 total
		length for a matched address.
		For different matched criteria, the testcase will move
		the ipv6 source address to the ethernet destination
		source address.

	Verification:
		The packet verification for the testcase should happen
		according to the description.