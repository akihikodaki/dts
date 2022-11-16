Test Case: test_u100_002
-----------------------

    Scenario being tested:
        In this usecase, we are testing the action profile feature for various type of packets.

    Description:
        The test case receives various type of packets like IPv4, TCP, UDP, ICMP, IGMP.
        Action profile is conconfigured to send the packet a particular port, perform l3
        switching, and to drop the packets. Different type of packets have different match
        fields. Also packet validation is also performed.

    Verification:
        The packet verification for the testcase should happen as per action profile configuration.
