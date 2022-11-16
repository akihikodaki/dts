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
	bit<48> addr
}

metadata instanceof metadata_t

//
// Actions
//
struct add_008_args_t {
	bit<48> value
}

action add_008_action args instanceof add_008_args_t {
	mov m.addr h.ethernet.src_addr
	add m.addr t.value
	mov h.ethernet.src_addr m.addr
	return
}

action drop args none {
	drop
}

//
// Table
//
table add_008 {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		add_008_action
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
	table add_008
	emit h.ethernet
	tx m.port
}
