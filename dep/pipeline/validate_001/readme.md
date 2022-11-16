Test Case: validate_001
-----------------------

    Instructions being tested:
        validate h.header

    Description:
        For the received packet, if its ttl is greater than 0x00, decrement it and transmit it back on the same port. Else if i
        ttl is zero and its destination ipv4 address is 0xaabbccdd, update the ttl value as 0x50 and transmit the packet back on
        the same port. Drop all other packets.

    Verification:
        For packets received with ttl value grater than 0x00, ttl should be decremented by one. For packets received with ttl value
        equal to 0x00 and destination ipv4 address as 0xaabbccdd, ttl should be updated to 0x50. All other packets should be dropped.
