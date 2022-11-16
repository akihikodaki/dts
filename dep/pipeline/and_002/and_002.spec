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
struct src_pat_args_t {
	bit<32> port
}

action and_002_action args instanceof src_pat_args_t {
	and m.port t.port
	return
}

action drop args none {
	drop
}

//
//table
//
table and_002 {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		and_002_action
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
	table and_002
	emit h.ethernet
	tx m.port
}
