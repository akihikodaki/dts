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
	bit<48> val_48
	bit<48> val_32
	bit<48> val_16
	bit<48> val_8
}

metadata instanceof metadata_t

//
// Registers.
//
regarray REG_ARR_1 size 0x1FFFFFF initval 0

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	regrd m.val_48 REG_ARR_1 0x1a1a2a3
	regrd m.val_32 REG_ARR_1 0x7fb1b2
	regrd m.val_16 REG_ARR_1 0x7fc1
	regrd m.val_8 REG_ARR_1 0x7f
	regwr REG_ARR_1 0xa3a4 m.val_48
	regwr REG_ARR_1 0xb3b4 m.val_32
	regwr REG_ARR_1 0xc2 m.val_16
	regwr REG_ARR_1 0xd2 m.val_8
	emit h.ethernet
	tx m.port
}
