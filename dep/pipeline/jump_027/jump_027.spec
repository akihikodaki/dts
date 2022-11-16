;SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2010-2020 Intel Corporation

//
// Headers
//
struct ethernet_h {
        bit<48> dst_addr
        bit<48> src_addr
        bit<16> ethertype
}

struct ipv4_h {
    bit<8> ver_ihl
    bit<8> diffserv
    bit<16> total_len
    bit<16> identification
    bit<16> flags_offset
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
	bit<32> ether_type
}

metadata instanceof metadata_t

//
// Actions
//
struct jump_027_args_t {
    bit<32> ether_type
}

action jump_027_action args instanceof jump_027_args_t {
	mov m.ether_type h.ethernet.ethertype
    jmpeq LABEL_0 t.ether_type m.ether_type
	mov m.port 4
	LABEL_0 : mov h.ipv4.src_addr 0x42424242
    return
}

action drop args none {
    drop
}

//
//table
//
table jump_027_table {
    key {
        h.ethernet.dst_addr exact
    }

    actions {
        jump_027_action
        drop
    }

    default_action drop args none
    size 1048576
}

//
// Pipeline
//
apply {
    rx m.port
    extract h.ethernet
	extract h.ipv4
    table jump_027_table
    emit h.ethernet
	emit h.ipv4
    tx m.port
}
