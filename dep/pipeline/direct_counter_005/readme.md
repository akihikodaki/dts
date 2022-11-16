Test Case: direct_counter_005
-----------------------------

Instruction being tested:
    entryid m.table_entry_index

Scenario being tested:
   Learner table with a multiple parameters as a key.
   The key structure is metadata.

Description:
    Increment the counter (packet) value at specific index in the
    register array. This register array is allocated for the specific
    table to support table property "pna_direct_counter or
    psa_direct_counter".
    The 'entryid' instruction gets the index from the table lookup of
    the current packet. This will identify the unique location in the
    register array to maintain the counter for the table entry that
    is hit.

Verification:
    Read the VALUE from the CLI with register index (Table entry as
    a key is not available in CLI for learner table) and it should
    match the number that an entry in the table hit.
