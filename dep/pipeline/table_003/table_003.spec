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
struct table_003_args_t {
	bit<48> ethernet_dst_addr
	bit<48> ethernet_src_addr
	bit<16> ethernet_ethertype
}

action table_003_action_01 args instanceof table_003_args_t {
	mov h.ethernet.dst_addr t.ethernet_dst_addr
	mov h.ethernet.src_addr t.ethernet_src_addr
	mov h.ethernet.ethertype t.ethernet_ethertype
    validate h.ethernet
    return
}

action table_003_action_02 args instanceof table_003_args_t {
	mov h.ethernet.dst_addr t.ethernet_dst_addr
	mov h.ethernet.src_addr t.ethernet_src_addr
	mov h.ethernet.ethertype t.ethernet_ethertype
    validate h.ethernet
    xor m.port 1
	return
}

action drop args none {
    drop
}

//
// Tables.
//
table table_003_table {
	key {
		h.ethernet.dst_addr wildcard
	}

	actions {
		table_003_action_01
		table_003_action_02
		drop
	}

	default_action drop args none
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	table table_003_table
	emit h.ethernet
	tx m.port
}
