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
    bit<32> count_packet
    bit<32> color_in
    bit<32> color_out
    bit<32> timeout_id
}

metadata instanceof metadata_t

//
// Actions
//
action direct_meter_003_action args none {
    entryid m.table_entry_index
    mov m.count_packet 1
    mov m.color_in 0
    meter MET_DIRECT_METER_003 m.table_entry_index m.count_packet m.color_in m.color_out
    return
}

action drop args none {
    jmpneq DROP m.ipv4_src_addr 0x01010101
    jmpneq DROP m.ipv4_dst_addr 0x0a0a0a01
    mov m.timeout_id 0
    learn direct_meter_003_action m.timeout_id
    DROP : drop
}

//
// Tables.
//
learner direct_meter_003 {
    key {
        m.ipv4_src_addr
        m.ipv4_dst_addr
    }

    actions {
        direct_meter_003_action
        drop
    }

    default_action drop args none

    timeout {
        60
        120
        180
    }

    size 16
}

// Direct meter reference for the learner table direct_meter_003
metarray MET_DIRECT_METER_003 size 0x10

//
// Pipeline.
//
apply {
    rx m.port
    extract h.ethernet
    extract h.ipv4
    mov m.ipv4_src_addr h.ipv4.src_addr
    mov m.ipv4_dst_addr h.ipv4.dst_addr
    table direct_meter_003
    emit h.ethernet
    emit h.ipv4
    tx m.port
}