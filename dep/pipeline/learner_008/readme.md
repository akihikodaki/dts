Test Case: test_learner_008
-----------------------

    Scenario being tested:
        learn <action_name> <action_argument:optional> m.field
        rearm m.field

    Description:
        The learner table, has timeout configurations as 30,60 and 120 seconds.
        For the first packet, the application expects a miss, a default action will
        be taken place. The default action will add/learn entry with timeout as 30 seconds.
        The default action will transmit packet to port 0.
        The same packet is sent again, this time we expect the learnt action to take place.
        The learn action will update the existing learnt timer with 120 seconds using 'rearm
        m.field' instruction. The learnt action will transmit the packet to port 1.
        The testcase waits for 60 seconds to validate the updated time.
        Two packets, one with similar match key for which the timer was updated along with a
        new packet is sent, with the expectations of learnt action to take place for the existing
        packet and default action to take place for new packet, by emitting packets on output port
        as 1 and 0 respectively.

    Verification:
        The packet verification for the testcase should happen according to the description.