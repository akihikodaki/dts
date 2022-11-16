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
	bit<16> ipv4_total_len
	bit<32> ipv4_dst_addr
	bit<16> ipv4_hdr_checksum
}

metadata instanceof metadata_t

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4

	mov m.ipv4_total_len h.ipv4.total_len
	mov m.ipv4_dst_addr h.ipv4.dst_addr
	mov m.ipv4_hdr_checksum h.ipv4.hdr_checksum
	sub h.ethernet.src_addr m.ipv4_total_len
	sub h.ipv4.src_addr m.ipv4_dst_addr
	sub h.ipv4.ttl m.ipv4_hdr_checksum
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
