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
	bit<32> addr
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
table jump_030 {
	key {
	}

	actions {
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
	mov m.addr h.ipv4.dst_addr
	jmpeq LABEL_0 m.addr 0xaa0000bb
	table jump_030
	LABEL_0 : emit h.ethernet
	emit h.ipv4
	tx m.port
}
