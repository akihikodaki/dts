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
	regwr REG_ARR_1 h.ipv4.identification h.ethernet.dst_addr
	regwr REG_ARR_1 h.ipv4.flags_offset h.ipv4.src_addr
	regwr REG_ARR_1 h.ipv4.diffserv h.ipv4.total_len
	regwr REG_ARR_1 h.ipv4.ttl h.ipv4.protocol
    emit h.ethernet
	emit h.ipv4
	tx m.port
}
