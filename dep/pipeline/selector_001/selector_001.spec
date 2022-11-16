; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2020 Intel Corporation

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
	bit<32> port_in
	bit<32> port_out
	bit<32> group_id
}

metadata instanceof metadata_t

//
// Tables
//
selector selector_001 {
	group_id m.group_id

	selector {
		h.ipv4.protocol
		h.ipv4.src_addr
		h.ipv4.dst_addr
	}

	member_id m.port_out

	n_groups_max 2
	n_members_per_group_max 8
}

//
// Pipeline.
//
apply {
	rx m.port_in
	extract h.ethernet
	extract h.ipv4
	mov m.group_id h.ethernet.dst_addr
	table selector_001
	emit h.ethernet
	emit h.ipv4
	tx m.port_out
}
