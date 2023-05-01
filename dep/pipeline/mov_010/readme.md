Test Case: test_mov_010
-----------------------

	Instructions being tested:
		mov (h/m).field h.field

	Scenario being tested:
		mov dst src
		dst : 128 bit header or metadata
		src : <= 64 bit header field (64, 48, 32, 16, 8)

	Description:
		The testcase moves ipv4 source address to the ipv6
		destination address and ipv6 payload length to the ipv6
		source address for a matched address.
		For second matched criteria, the testcase will move the
		ethernet source address to the ipv6 source address.
		For the third matched criteria, the testcase will move the
		64-bit ipv4 header data to ipv6 source address and ipv4 ttl
		to the ipv6 destination address.
		For the fourth matched criteria, the testcase will move the
		64-bit ipv4 header data to ipv6 source address and ipv4 ttl
		to the ipv6 destination address.

	Verification:
		The packet verification for the testcase should happen
		according to the description.