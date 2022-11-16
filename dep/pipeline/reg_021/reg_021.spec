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

header ethernet instanceof ethernet_h

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
struct reg_021_args_t {
	bit<32> idx_64
	bit<32> idx_48
	bit<32> idx_32
	bit<32> idx_16
	bit<32> idx_8
}

action reg_021_action args instanceof reg_021_args_t {
	regwr REG_ARR_1 t.idx_64 0x1234567890123456
	regwr REG_ARR_1 t.idx_48 0x123456789012
	regwr REG_ARR_1 t.idx_32 0x12345678
	regwr REG_ARR_1 t.idx_16 0x1234
	regwr REG_ARR_1 t.idx_8 0x12
	return
}

action drop args none {
    drop
}

//
// Tables.
//
table reg_021 {
	key {
		h.ethernet.ethertype exact
	}

	actions {
		reg_021_action
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
	table reg_021
	emit h.ethernet
	tx m.port
}
