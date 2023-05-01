Test Case: test_mov_009
-----------------------

	Instructions being tested:
		mov (h/m).field (h/m).field

	Scenario being tested:
		mov dst src
		dst : 128 bit header or metadata
		src : 128 bit header or metadata

	Description:
		The testcase swaps the ipv6 source address with ipv6
		destination address.

	Verification:
		The packet verification for the testcase should happen
		according to the description.