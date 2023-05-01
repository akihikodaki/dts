; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2023 Intel Corporation

//
// Headers
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

struct udp_h {
	bit<16> src_port
	bit<16> dst_port
	bit<16> length
	bit<16> checksum
}

header ethernet instanceof ethernet_h
header ipv4 instanceof ipv4_h
header udp instanceof udp_h

//
// Meta-data.
//
struct metadata_t {
	bit<32> port
	bit<32> hash
	bit<8> ipv4_protocol
	bit<32> ipv4_src_addr
	bit<32> ipv4_dst_addr
	bit<16> udp_src_port
	bit<16> udp_dst_port
}

metadata instanceof metadata_t

//
// RSS.
//
rss rss0

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4

	// Collect packet fields for RSS hash compute
	mov m.ipv4_protocol h.ipv4.protocol
	mov m.ipv4_src_addr h.ipv4.src_addr
	mov m.ipv4_dst_addr h.ipv4.dst_addr
	mov m.udp_src_port h.udp.src_port
	mov m.udp_dst_port h.udp.dst_port

	// Using metadata fields for RSS hash calculation
	rss rss0 m.hash m.ipv4_protocol m.udp_dst_port

	and m.hash 3
	mov m.port m.hash
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
