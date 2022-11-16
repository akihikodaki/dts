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
// Packet meta-data.
//
struct metadata_t {
	bit<32> port
	bit<48> addr_48
	bit<32> addr_32
	bit<16> addr_16
}

metadata instanceof metadata_t

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4

	// exchange ipv4 src and dest addresses
	mov m.addr_48 h.ipv4.dst_addr // >
	mov h.ipv4.dst_addr h.ipv4.src_addr
	mov h.ipv4.src_addr m.addr_48 // <

	// exchange ethernet src and dest addresses
	mov m.addr_32 h.ethernet.dst_addr // <
	mov h.ethernet.dst_addr h.ethernet.src_addr
	mov h.ethernet.src_addr m.addr_32 // >

	// exchange ipv4 identification and flags_offset
	mov m.addr_16 h.ipv4.identification // ==
	mov h.ipv4.identification h.ipv4.flags_offset
	mov h.ipv4.flags_offset m.addr_16 // ==

	emit h.ethernet
	emit h.ipv4
	tx m.port
}
