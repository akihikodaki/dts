; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2020 Intel Corporation

//
// Packet headers.
//
struct ethernet_h {
	bit<48> dst_addr
	bit<48> src_addr
	bit<16> ether_type
}

header ethernet instanceof ethernet_h

//
// Packet meta-data.
//
struct metadata_t {
	bit<32> port
}

metadata instanceof metadata_t

//
// Actions
//

action action_001 args none {
	return
}

action action_002 args none {
	return
}

action default_001 args none {
	drop
}

action default_002 args none {
	return
}

//
// Tables.
//

table annotation_003 {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		action_001 @tableonly @defaultonly
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
	table annotation_003
	emit h.ethernet
	tx m.port
}