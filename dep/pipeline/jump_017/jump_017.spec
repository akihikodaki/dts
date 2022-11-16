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
action drop args none {
    drop
}

//
// Tables.
//
table jump_017 {
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
	jmpgt LABEL_0 h.ethernet.dst_addr h.ipv4.src_addr // >
	table jump_017
	LABEL_0 : jmpgt LABEL_1 h.ethernet.dst_addr h.ethernet.src_addr // =
	table jump_017
	LABEL_1 : jmpgt LABEL_2 h.ipv4.dst_addr h.ethernet.src_addr // <
	table jump_017
	LABEL_2 : emit h.ethernet
	emit h.ipv4
	tx m.port
}
