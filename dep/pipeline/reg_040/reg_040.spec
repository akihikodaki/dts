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
struct reg_040_args_t {
	bit<64> val_64
	bit<48> val_48
	bit<32> val_32
	bit<16> val_16
	bit<8> val_8
}

action reg_040_action args instanceof reg_040_args_t {
	regadd REG_ARR_1 0x1a1a2a3 t.val_64
	regadd REG_ARR_1 0x7fb1b2 t.val_48
	regadd REG_ARR_1 0x7fc1 t.val_32
	regadd REG_ARR_1 0x7f t.val_16
	regadd REG_ARR_1 0xf7 t.val_8
	return
}

action drop args none {
    drop
}

//
// Tables.
//
table reg_040 {
	key {
		h.ethernet.ethertype exact
	}

	actions {
		reg_040_action
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
	table reg_040
	emit h.ethernet
	tx m.port
}
