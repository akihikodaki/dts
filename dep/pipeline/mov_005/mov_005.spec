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
struct mov_005_args_t {
	bit<32> port_out
}

action mov_005_action args instanceof mov_005_args_t {
	mov m.port t.port_out
	return
}

action drop args none {
	drop
}

//
//table
//
table mov_005 {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		mov_005_action
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
	table mov_005
	emit h.ethernet
	tx m.port
}
