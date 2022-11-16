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
    bit<8> ipv4_protocol
    bit<32> table_entry_index
    bit<32> color_in
    bit<32> color_out
}

metadata instanceof metadata_t

//
// Actions
//
action direct_meter_002_action args none {
    entryid m.table_entry_index
    mov m.color_in 0
    meter MET_DIRECT_METER_002 m.table_entry_index h.ipv4.total_len m.color_in m.color_out
    return
}

action drop args none {
    drop
}

//
// Tables.
//
table direct_meter_002 {
    key {
        m.ipv4_dst_addr exact
        m.ipv4_protocol exact
        m.ipv4_src_addr exact
    }

    actions {
        direct_meter_002_action
        drop
    }

    default_action drop args none
    size 65536
}

// Direct meter reference for the table direct_meter_002
metarray MET_DIRECT_METER_002 size 0x10001

//
// Pipeline.
//
apply {
    rx m.port
    extract h.ethernet
    extract h.ipv4
    mov m.ipv4_dst_addr h.ipv4.dst_addr
    mov m.ipv4_protocol h.ipv4.protocol
    mov m.ipv4_src_addr h.ipv4.src_addr
    table direct_meter_002
    emit h.ethernet
    emit h.ipv4
    tx m.port
}