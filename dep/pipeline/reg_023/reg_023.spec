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
	bit<64> val_64
	bit<48> val_48
	bit<32> val_32
	bit<16> val_16
	bit<8> val_8
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
	jmpneq L1 h.ethernet.ethertype 0x08aa
    mov m.val_64 0x1234567890123456
	mov m.val_48 0x123456789012
	mov m.val_32 0x12345678
	mov m.val_16 0x1234
	mov m.val_8 0x12
	regwr REG_ARR_1 0x1a1a2a3 m.val_64
	regwr REG_ARR_1 0x7fb1b2 m.val_48
	regwr REG_ARR_1 0x7fc1 m.val_32
	regwr REG_ARR_1 0x7f m.val_16
	regwr REG_ARR_1 0xf7 m.val_8
	L1 : emit h.ethernet
	tx m.port
}
