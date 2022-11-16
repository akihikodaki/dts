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
action extract_emit_009_action args none {
	return
}

//
// Tables.
//
table extract_emit_009 {
	key {
	}

	actions {
		extract_emit_009_action
	}

	default_action extract_emit_009_action args none const
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	table extract_emit_009
	emit h.ethernet
	table extract_emit_009
	tx m.port
}
