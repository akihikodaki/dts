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

header ethernet instanceof ethernet_h

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
struct table_008_args_t {
	bit<48> ethernet_src_addr
}

action table_008_action_01 args instanceof table_008_args_t {
	mov h.ethernet.src_addr t.ethernet_src_addr
	return
}

action table_008_default_action_01 args none {
	mov h.ethernet.dst_addr 0x112233445566
	mov h.ethernet.src_addr 0xaabbccddeeff
	mov h.ethernet.ethertype 0x0800
	return
}

struct table_008_default_args_t {
	bit<48> dst_addr
	bit<48> src_addr
	bit<16> ethertype
}

action table_008_default_action_02 args instanceof table_008_default_args_t {
	mov h.ethernet.dst_addr t.dst_addr
	mov h.ethernet.src_addr t.src_addr
	mov h.ethernet.ethertype t.ethertype
	return
}

//
// Tables.
//
table table_008_table {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		table_008_action_01
		table_008_default_action_01
		table_008_default_action_02
	}

	default_action table_008_default_action_01 args none
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	table table_008_table
	emit h.ethernet
	tx m.port
}
