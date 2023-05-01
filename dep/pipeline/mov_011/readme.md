Test Case: test_mov_011
-----------------------

	Instructions being tested:
		mov h.field (h/m).field

	Scenario being tested:
		mov dst src
		dst : <= 64 bit header field (64, 48, 32, 16, 8)
		src : 128 bit header or metadata

	Description:
		The testcase moves ipv6 destination address to the ipv4
		source address and ipv6 source address to the ipv6 payload
		length for a matched address.
		For second matched criteria, the testcase will move
		the ipv6 source address to the ethernet source address.
		For third matched criteria, the testcase will move
		ipv6 source address to 64-bit value ipv4 header field and
		move ipv6 destination address to ipv4 ttl.
		For fourth matched criteria, the testcase will move
		ipv6 source address to 64-bit value ipv4 header field and
		move ipv6 destination address to ipv4 ttl.

	Verification:
		The packet verification for the testcase should happen
		according to the description.