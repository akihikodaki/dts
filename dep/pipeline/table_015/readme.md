Test Case: test_table_015
-----------------------

    Scenario being tested:
        Exact match table with key structure type as a metadata, match criteria as an
        exact match, key element alignment as contiguous and key size < 64 bytes.

    Description:
        The test case receives Ethernet -> IPv4 -> UDP -> VXLAN -> Ethernet -> IPv4 -> UDP
        packet sequence as an input. If the packet matches the configured action rule, the
        associated respective action must take place. If the packet does not match the specified
        criteria, the default action should take place.

    Verification:
        The packet verification for the testcase should happen according to the description.