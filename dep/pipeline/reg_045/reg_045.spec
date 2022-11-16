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
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4
	jmpneq L1 h.ethernet.src_addr 0x102233445566
	regprefetch REG_ARR_1 0xa1a2
	regprefetch REG_ARR_1 0xb1b2
	regprefetch REG_ARR_1 0xc1
	regprefetch REG_ARR_1 0xd1
	regadd REG_ARR_1 0xa1a2 h.ethernet.dst_addr
	regadd REG_ARR_1 0xb1b2 h.ipv4.src_addr
	regadd REG_ARR_1 0xc1 h.ipv4.total_len
	regadd REG_ARR_1 0xd1 h.ipv4.protocol
	L1 : emit h.ethernet
	emit h.ipv4
	tx m.port
}
