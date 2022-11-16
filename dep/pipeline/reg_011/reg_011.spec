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
	extract h.ipv4
	mov m.val_48 0x123456789012
	mov m.val_32 0x12345678
	mov m.val_16 0x1234
	mov m.val_8 0x06
	regwr REG_ARR_1 h.ipv4.identification m.val_48
	regwr REG_ARR_1 h.ipv4.flags_offset m.val_32
	regwr REG_ARR_1 h.ipv4.diffserv m.val_16
	regwr REG_ARR_1 h.ipv4.ttl m.val_8
    emit h.ethernet
	emit h.ipv4
	tx m.port
}
