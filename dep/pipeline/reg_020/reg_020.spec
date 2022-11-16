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
	bit<16> idx_48
	bit<16> idx_32
	bit<16> idx_16
	bit<16> idx_8
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
    mov m.idx_48 0xa1a2
	mov m.idx_32 0xb1b2
	mov m.idx_16 0xc1
	mov m.idx_8 0xd1
	regwr REG_ARR_1 m.idx_48 0x1234567890123456
	regwr REG_ARR_1 m.idx_32 0x123456789012
	regwr REG_ARR_1 m.idx_16 0x12345678
	regwr REG_ARR_1 m.idx_8 0x1234
	L1 : emit h.ethernet
	tx m.port
}
