
Test Case: test_or_005
----------------------

    Instruction being tested:
        or h.field m.field

    Description:
        For the received packet, bitwise OR destination MAC address,
        destination IP address and IP identification with a fixed value and
        transmit the packet back on the same port.

    Verification:
        Verify using input and output pcap files.
