Test Case: test_ipsec_001
-----------------------------

Scenario being tested:
    IPSEC SA rule addition for the tunnel mode.

Description:
    IPSEC block will be created in application, without any table
    rules and SA rules. The first packet sent, should not match
    any rule and should be dropped.
    The testcase then configure table rules as well as add SA rules
    using CLI commands. The same packet is sent, it should match the
    table rule, do encryption of the packet with the configured SA
    rules, do decryption of the encrypted packet based on the SA
    rule. The application will modify MAC addresses and sent out
    the modified packet on the same port.

Verification:
    The packet verification for the testcase should happen
    according to the description.
