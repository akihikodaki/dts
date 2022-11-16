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
	bit<32> member_id
}

metadata instanceof metadata_t

//
// Actions
//
struct profile_001_action_01_args_t {
	bit<32> member_id
}

struct profile_001_action_02_args_t {
	bit<32> port
	bit<48> new_mac_da
	bit<48> new_mac_sa
}

action drop args none {
	drop
}

action profile_001_action_01 args instanceof profile_001_action_01_args_t {
	mov m.member_id t.member_id
	return
}

action profile_001_action_02 args instanceof profile_001_action_02_args_t {
	mov h.ethernet.dst_addr t.new_mac_da
	mov h.ethernet.src_addr t.new_mac_sa
	cksub h.ipv4.hdr_checksum h.ipv4.ttl
	sub h.ipv4.ttl 0x1
	ckadd h.ipv4.hdr_checksum h.ipv4.ttl
	mov m.port_out t.port
	return
}

//
// Tables
//
table profile_001_table_01 {
	key {
		h.ipv4.dst_addr exact
	}

	actions {
		profile_001_action_01
		drop
	}

	default_action drop args none
	size 1048576
}

table profile_001_table_02 {
	key {
		m.member_id exact
	}

	actions {
		profile_001_action_02
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
	table profile_001_table_01
	table profile_001_table_02
	emit h.ethernet
	emit h.ipv4
	tx m.port_out
}
