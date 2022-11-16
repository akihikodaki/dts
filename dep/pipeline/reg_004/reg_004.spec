; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2021 Intel Corporation

//
// Headers.
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
// Meta-data.
//
struct metadata_t {
	bit<32> port
}

metadata instanceof metadata_t

//
// Registers.
//
regarray REG_ARR_1 size 0x1FFFFFF initval 0

//
// Actions
//
struct reg_004_args_t {
	bit<32> idx_48
	bit<32> idx_32
	bit<32> idx_16
	bit<32> idx_8
}

action reg_004_action args instanceof reg_004_args_t {
	regrd h.ethernet.dst_addr REG_ARR_1 t.idx_48
	regrd h.ipv4.src_addr REG_ARR_1 t.idx_32
	regrd h.ipv4.identification REG_ARR_1 t.idx_16
	regrd h.ipv4.ttl REG_ARR_1 t.idx_8
	return
}

action drop args none {
    drop
}

//
// Tables.
//
table reg_004 {
	key {
	    h.ethernet.src_addr exact
    }

	actions {
		reg_004_action
		drop
	}

	default_action drop args none
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4
	table reg_004
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
