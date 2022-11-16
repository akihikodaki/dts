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
	bit<8> ipv4_ttl
}

metadata instanceof metadata_t

//
// Actions
//
struct jump_026_args_t {
	bit<8> ipv4_ttl
}

action jump_026_action args instanceof jump_026_args_t {
	mov m.ipv4_ttl h.ipv4.ttl
	jmpeq LABEL_0 m.ipv4_ttl t.ipv4_ttl
	sub h.ipv4.ttl 0x01
	return
	LABEL_0 : drop
}

action drop args none {
    drop
}

//
// Tables.
//
table jump_026 {
	key {
		h.ethernet.ether_type exact
	}

	actions {
		jump_026_action
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
	table jump_026
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
