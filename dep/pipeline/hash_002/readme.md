Test Case: test_hash_002
-----------------------

    Instruction being tested:
        hash crc32 m.field m.field m.field

    Description:
        Hash is calculated using the crc32 algorithm on metadata fields.

    Verification:
        Packet sent to the output port on the basis of last two bits of the calculted hash value.
