Test Case: direct_meter_002
-----------------------------

Instruction being tested:
    entryid m.table_entry_index

Scenario being tested:
    Regular table with a multiple parameters as a key.
    The key structure is metadata, with key elements
    are in non-consecutive order.

Description:
    Increment the meter value (bytes in ipv4 packet length) at specific
    index in the meter array. This meter array is allocated for the
    specific table to support table property "pna_direct_meter or
    psa_direct_meter".
    The 'entryid' instruction gets the index from the table lookup
    of the current packet. This will identify the unique location in
    the meter array to maintain the meter stats for the table entry
    that is hit.

Verification:
    Read the VALUE from the CLI with table entry information and it
    should match the meter stats that each entry in the table hit.