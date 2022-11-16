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
	bit<32> port_in
	bit<32> port_out
	bit<16> ip_byte_count
	bit<8> color_in
}

metadata instanceof metadata_t

//
// Meters.
//
metarray MET_ARRAY_1 size 64

//
// Pipeline.
//
apply {
	rx m.port_in
	extract h.ethernet
	extract h.ipv4
	jmpeq L1 h.ethernet.dst_addr 0xaabbccdd0000
	mov m.port_out m.port_in
	jmp L2
	L1 : mov m.ip_byte_count h.ipv4.total_len
	mov m.color_in 0x0
	meter MET_ARRAY_1 h.ipv4.diffserv m.ip_byte_count m.color_in m.port_out
	L2 : emit h.ethernet
	emit h.ipv4
	tx m.port_out
}
