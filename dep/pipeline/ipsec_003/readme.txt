Test Case: test_ipsec_003
-----------------------------

Scenario being tested:
    IPSEC SA rule deletion for the tunnel mode.

Description:
    IPSEC block will be created in application, with matching table
    rules and SA rules. The first packet sent, should match the
    specified table rule, do encryption of the packet with the
    configured SA rule, do decryption of the encrypted packet based
    on the SA rule. The application will modify MAC addresses and
    sent out the modified packet on the same port.
    The testcase then delete the table rules as well as SA rules
    using CLI commands. The same packet is sent, it should not match
    any rule and should be dropped.

Verification:
    The packet verification for the testcase should happen
    according to the description.
