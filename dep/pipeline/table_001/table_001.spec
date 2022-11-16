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
// Actions.
//
action table_001_action args none {
	mov h.ethernet.src_addr h.ethernet.dst_addr
	return
}

//
// Tables.
//
table table_001 {
	key {
	}

	actions {
		table_001_action
	}

	default_action table_001_action args none const
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	table table_001
	emit h.ethernet
	tx m.port
}
