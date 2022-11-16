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
	bit<32> idx_64
	bit<32> idx_48
	bit<32> idx_32
	bit<32> idx_16
	bit<32> idx_8
}

metadata instanceof metadata_t

//
// Registers.
//
regarray REG_ARR_1 size 0x1FFFFFF initval 0

//
// Actions
//
struct reg_033_args_t {
	bit<64> val_64
	bit<48> val_48
	bit<32> val_32
	bit<16> val_16
	bit<8> val_8
}

action reg_033_action args instanceof reg_033_args_t {
	mov m.idx_64 0x1a1a2a3
	mov m.idx_48 0x7fb1b2
	mov m.idx_32 0x7fc1
	mov m.idx_16 0x7f
	mov m.idx_8 0xf7
	regadd REG_ARR_1 m.idx_64 t.val_64
	regadd REG_ARR_1 m.idx_48 t.val_48
	regadd REG_ARR_1 m.idx_32 t.val_32
	regadd REG_ARR_1 m.idx_16 t.val_16
	regadd REG_ARR_1 m.idx_8 t.val_8
	return
}

action drop args none {
    drop
}

//
// Tables.
//
table reg_033 {
	key {
		h.ethernet.ethertype exact
	}

	actions {
		reg_033_action
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
	table reg_033
	emit h.ethernet
	tx m.port
}
