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
    bit<32> table_entry_index
    bit<32> count_packet
    bit<32> color_in
    bit<32> color_out
}

metadata instanceof metadata_t

//
// Actions
//
action direct_meter_001_action args none {
    entryid m.table_entry_index
    mov m.count_packet 1
    mov m.color_in 0
    meter MET_DIRECT_METER_001 m.table_entry_index m.count_packet m.color_in m.color_out
    return
}

action drop args none {
    drop
}

//
// Tables.
//
table direct_meter_001 {
    key {
        h.ipv4.src_addr exact
        h.ipv4.dst_addr exact
    }

    actions {
        direct_meter_001_action
        drop
    }

    default_action drop args none
    size 65536
}

// Direct meter reference for the table direct_meter_001
metarray MET_DIRECT_METER_001 size 0x10001

//
// Pipeline.
//
apply {
    rx m.port
    extract h.ethernet
    extract h.ipv4
    table direct_meter_001
    emit h.ethernet
    emit h.ipv4
    tx m.port
}
