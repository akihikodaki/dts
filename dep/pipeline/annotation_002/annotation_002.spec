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
struct annotation_002_args_t {
	bit<48> ethernet_dst_addr
}

action action_001 args instanceof annotation_002_args_t {
	mov h.ethernet.dst_addr t.ethernet_dst_addr
	return
}

action action_002 args none {
	drop
}

action default_001 args none {
	drop
}

action default_002 args none {
	drop
}

//
// Tables.
//
table annotation_002 {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		action_001
		action_002
		default_001
		default_002
	}

	default_action default_001 args none

	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	table annotation_002
	emit h.ethernet
	tx m.port
}
