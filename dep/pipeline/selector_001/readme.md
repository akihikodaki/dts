Test Case: test_selector_002
----------------------------

    Description:

        In this simple example, the base table and the member table are striped out in order to focus
        exclusively on illustrating the selector table. The group_id is read from the destination MAC
        address and the selector n-tuple is represented by the Protocol, the source IP address and the
        destination IP address fields. The member_id produced by the selector table is used to identify
        the output port which facilitates the testing of different member weights by simply comparing the
        rates of output packets sent on different ports.
