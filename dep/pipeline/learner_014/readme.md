Test Case: test_learner_014
-----------------------

    Scenario being tested:
        Learner table with key structure type as a header, key element alignment as
        contiguous and key size > 64 bytes.

    Description:
        The test case receives Ethernet -> IPv6 -> UDP -> VXLAN -> Ethernet -> IPv6 -> UDP
        packet sequence as an input. The first packet will take the default action and learn
        the respective action. The second packet is resent before the expiration of timeout,
        executing the learnt action.

    Verification:
        The packet verification for the testcase should happen according to the description.