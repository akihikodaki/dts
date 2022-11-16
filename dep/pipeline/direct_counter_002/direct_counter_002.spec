; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2022 Intel Corporation

//
// Headers
//
struct ethernet_h {
    bit<48> dst_addr
    bit<48> src_addr
    bit<16> ethertype
}

struct ipv4_h {
    bit<8> version_ihl
    bit<8> diffserv
    bit<16> total_len
    bit<16> identification
    bit<16> flags_frag_offset
    bit<8> ttl
    bit<8> protocol
    bit<16> hdr_checksum
    bit<32> src_addr
    bit<32> dst_addr
}

header ethernet instanceof ethernet_h
header ipv4 instanceof ipv4_h

//
// Meta-data
//
struct metadata_t {
    bit<32> port
    bit<32> ipv4_src_addr
    bit<32> ipv4_dst_addr
    bit<32> table_entry_index
}

metadata instanceof metadata_t

//
// Actions
//
action direct_counter_002_action args none {
    entryid m.table_entry_index
    regadd REG_DIRECT_COUNTER_002 m.table_entry_index 1
    return
}

action drop args none {
    drop
}

//
// Tables.
//
table direct_counter_002 {
    key {
        m.ipv4_src_addr exact
        m.ipv4_dst_addr exact
    }

    actions {
        direct_counter_002_action
        drop
    }

    default_action drop args none
    size 65536
}

// Define the register upfront for direct counter based on registers
// The size of the register array is table size + 1 (for default entry)
regarray REG_DIRECT_COUNTER_002 size 0x10001 initval 0

//
// Pipeline.
//
apply {
    rx m.port
    extract h.ethernet
    extract h.ipv4
    mov m.ipv4_src_addr h.ipv4.src_addr
    mov m.ipv4_dst_addr h.ipv4.dst_addr
    table direct_counter_002
    emit h.ethernet
    emit h.ipv4
    tx m.port
}
