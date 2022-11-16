; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2010-2020 Intel Corporation

//
// Headers
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
// Meta-data
//
struct metadata_t {
	bit<32> port
}

metadata instanceof metadata_t

//
// Actions
//
struct shr_007_args_t {
	bit<8> addr
}

action shr_007_action args instanceof shr_007_args_t {
	shr h.ipv4.src_addr t.addr
	return
}

action drop args none {
	drop
}

//
// Table
//
table shr_007 {
	key {
		h.ipv4.dst_addr exact
	}

	actions {
		shr_007_action
		drop
	}

	default_action drop args none
	size 1048576
}

//
// Pipeline
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4
	table shr_007
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
