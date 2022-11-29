Test Case: validate_002
-----------------------

    Instructions being tested:
        validate h.header

    Description:
        For the received packet, if its ether type is 8100 then add a new ethernet header
        on the top of the packet. Otherwise drop the packet.

    Verification:
        The packet with ether type 0806 should be received with a new header on top.
