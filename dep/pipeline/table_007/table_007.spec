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
struct table_007_args_t {
	bit<48> ethernet_src_addr
}

action table_007_action_01 args instanceof table_007_args_t {
	mov h.ethernet.src_addr t.ethernet_src_addr
	return
}

struct table_007_default_args_t {
	bit<48> dst_addr
	bit<48> src_addr
	bit<16> ethertype
}

action table_007_default_action_01 args instanceof table_007_default_args_t {
	mov h.ethernet.dst_addr t.dst_addr
	mov h.ethernet.src_addr t.src_addr
	mov h.ethernet.ethertype t.ethertype
	return
}

//
// Tables.
//
table table_007_table {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		table_007_action_01
		table_007_default_action_01
	}

	default_action table_007_default_action_01 args dst_addr 0x112233445566 src_addr 0xaabbccddeeff ethertype 0x0800
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	table table_007_table
	emit h.ethernet
	tx m.port
}
