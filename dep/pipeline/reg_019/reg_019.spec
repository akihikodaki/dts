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
struct reg_019_args_t {
	bit<32> idx_64
	bit<32> idx_48
	bit<32> idx_32
	bit<32> idx_16
	bit<32> idx_8
	bit<64> val_64
	bit<48> val_48
	bit<32> val_32
	bit<16> val_16
	bit<8> val_8
}

action reg_019_action args instanceof reg_019_args_t {
	regwr REG_ARR_1 t.idx_64 t.val_64
	regwr REG_ARR_1 t.idx_48 t.val_48
	regwr REG_ARR_1 t.idx_32 t.val_32
	regwr REG_ARR_1 t.idx_16 t.val_16
	regwr REG_ARR_1 t.idx_8 t.val_8
	return
}

action drop args none {
    drop
}

//
// Tables.
//
table reg_019 {
	key {
		h.ethernet.ethertype exact
	}

	actions {
		reg_019_action
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
	table reg_019
	emit h.ethernet
	tx m.port
}
