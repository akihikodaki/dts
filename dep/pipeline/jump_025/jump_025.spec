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
}

metadata instanceof metadata_t

//
// Actions
//
struct jump_025_args_t {
	bit<8> ipv4_protocol
}

action jump_025_action args instanceof jump_025_args_t {
	jmpeq LABEL_0 h.ipv4.protocol t.ipv4_protocol
	mov m.port 4
	LABEL_0 : return
}

action drop args none {
    drop
}

//
// Tables.
//
table jump_025 {
	key {
		h.ethernet.ether_type exact
	}

	actions {
		jump_025_action
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
	table jump_025
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
