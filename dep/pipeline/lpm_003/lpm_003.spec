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
	bit<8> version_ihl
	bit<8> diffserv
	bit<16> total_len
	bit<16> identification
	bit<16> flags_frag_offset
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
	bit<32> vrf_id
	bit<32> dst_addr
}
metadata instanceof metadata_t

//
// Actions
//
struct lpm_003_args_t {
	bit<32> port_out
}

action lpm_003_action args instanceof lpm_003_args_t {
	mov m.port_out t.port_out
	return
}

action drop args none {
	drop
}

//
// Tables.
//
table lpm_003_table {
	key {
		m.vrf_id exact
		m.dst_addr lpm
	}

	actions {
		lpm_003_action
		drop
	}

	default_action drop args none
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port_in
	extract h.ethernet
	extract h.ipv4
	mov m.vrf_id h.ipv4.src_addr
	mov m.dst_addr h.ipv4.dst_addr
	table lpm_003_table
	emit h.ethernet
	emit h.ipv4
	tx m.port_out
}
