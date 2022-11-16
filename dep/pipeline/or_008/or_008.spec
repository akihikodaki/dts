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
struct or_008_args_t {
	bit<32> port
}

action or_008_action args instanceof or_008_args_t {
	or m.port t.port
	return
}

action drop args none {
	drop
}

//
// Table
//
table or_008 {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		or_008_action
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
	table or_008
	emit h.ethernet
	tx m.port
}
