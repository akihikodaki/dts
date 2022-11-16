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
action validate_001_action args none {
	return
}

action drop args none {
    drop
}

//
// Tables.
//
table validate_001 {
	key {
		h.ipv4.ttl exact
	}

	actions {
		validate_001_action
		drop
	}

	default_action validate_001_action args none
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4
	jmpgt LABEL_1 h.ipv4.ttl 0x00
	jmpeq LABEL_0 h.ipv4.dst_addr 0xaabbccdd
	invalidate h.ipv4
	table validate_001
	LABEL_0 : validate h.ipv4
	mov h.ipv4.ttl 0x51
	LABEL_1 : jmpnv LABEL_2 h.ipv4
	sub h.ipv4.ttl 0x01
	LABEL_2 : table validate_001
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
