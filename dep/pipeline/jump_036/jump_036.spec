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
}

metadata instanceof metadata_t

//
// Actions
//
struct jump_036_args_t {
	bit<48> ipv4_ttl
}

action jump_036_action args instanceof jump_036_args_t {
	jmpneq LABEL_0 h.ipv4.ttl t.ipv4_ttl
	mov m.port 4
	return
	LABEL_0 : sub h.ipv4.ttl 0x01
	return
}

action drop args none {
	drop
}

//
// Tables.
//
table jump_036 {
	key {
		h.ethernet.ether_type exact
	}

	actions {
		jump_036_action
		drop
	}

	default_action drop args none const
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4
	table jump_036
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
