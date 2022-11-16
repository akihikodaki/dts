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
struct reg_028_args_t {
	bit<48> val_48
	bit<32> val_32
	bit<16> val_16
	bit<8> val_8
}

action reg_028_action args instanceof reg_028_args_t {
	regadd REG_ARR_1 h.ipv4.identification t.val_48
	regadd REG_ARR_1 h.ipv4.flags_offset t.val_32
	regadd REG_ARR_1 h.ipv4.diffserv t.val_16
	regadd REG_ARR_1 h.ipv4.ttl t.val_8
	return
}

action drop args none {
    drop
}

//
// Tables.
//
table reg_028 {
	key {
		h.ethernet.ethertype exact
	}

	actions {
		reg_028_action
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
	table reg_028
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
