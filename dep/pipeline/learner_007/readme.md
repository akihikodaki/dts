Test Case: test_learner_007
-----------------------

    Scenario being tested:
        learn <action_name> <action_argument:optional> m.field

    Description:
        The learner table, has timeout configurations as 30,60 and 120 seconds.
        For the first packet, the application expects a miss, a default action will
        be taken place. The default action will add/learn entry with timeout as 30 seconds.
        The default action will transmit packet to port 0.
        The same packet is sent again, this time we expect the learnt action to take place.
        The learnt action will transmit the packet to port 1.
        The testcase waits for 30 seconds to expire the added time. The packet is sent again
        with the expectation of a Miss and a default action course with output port as 0.

    Verification:
        The packet verification for the testcase should happen according to the description.