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
	extract h.ipv4
	jmpneq L1 h.ethernet.ethertype 0x08aa
    regrd m.val_48 REG_ARR_1 h.ipv4.identification
	regrd m.val_32 REG_ARR_1 h.ipv4.flags_offset
	regrd m.val_16 REG_ARR_1 h.ipv4.diffserv
	regrd m.val_8 REG_ARR_1 h.ipv4.ttl
	regwr REG_ARR_1 0xa3a4 m.val_48
	regwr REG_ARR_1 0xb3b4 m.val_32
	regwr REG_ARR_1 0xc2 m.val_16
	regwr REG_ARR_1 0xd2 m.val_8
	L1 : emit h.ethernet
	emit h.ipv4
	tx m.port
}
