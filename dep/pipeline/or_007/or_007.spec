; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2020 Intel Corporation

//
// Packet headers.
//
struct ethernet_h {
	bit<48> dst_addr
	bit<48> src_addr
	bit<16> ether_type
}

header ethernet instanceof ethernet_h

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

header ipv4 instanceof ipv4_h

//
// Packet meta-data.
//
struct metadata_t {
	bit<32> port
	bit<32> addr_1
	bit<32> addr_2
}

metadata instanceof metadata_t

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4
	mov m.addr_1 h.ipv4.src_addr
	mov m.addr_2 h.ipv4.dst_addr
	or m.addr_1 0xF0F0F0F0
	or m.addr_2 0xF0F0F0F0
	mov h.ipv4.src_addr m.addr_1
	mov h.ipv4.dst_addr m.addr_2
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
