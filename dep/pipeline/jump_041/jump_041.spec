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
action jump_041_action args none {
	emit h.ethernet
	tx m.port
}

//
// Tables.
//
table jump_041 {
	key {
	}

	actions {
		jump_041_action
	}

	default_action jump_041_action args none const
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	jmpneq LABEL_0 h.ethernet.ether_type 0x0800
	table jump_041
	LABEL_0 : drop
}
