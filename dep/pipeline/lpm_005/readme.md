Test Case: test_lpm_005
-------------------------

    Scenario being tested:
    To test IPv6 address as table key field for LPM.

    Description:
        Copy the destination MAC address of the received packet into the source MAC address
        and transmit the packet back on the same port for the matched action.
        Copy the source MAC address of the received packet into the destination MAC address
        and transmit the packet back on the same port for the unmatched action.

    Verification:
        Packet verification should happen according to the description.