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
	bit<8> ttl_val
}

metadata instanceof metadata_t

//
// Actions
//
action drop args none {
    drop
}

//
// Tables.
//
table jump_018 {
	key {
	}

	actions {
		drop
	}

	default_action drop args none const
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4
	mov m.ttl_val h.ipv4.ttl
	jmpgt LABEL_0 m.ttl_val 0x00
	table jump_018
	LABEL_0 : sub m.ttl_val 0x01
	mov h.ipv4.ttl m.ttl_val
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
