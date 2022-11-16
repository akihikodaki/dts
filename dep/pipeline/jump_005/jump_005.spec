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
action jump_005_action args none {
	return
}

//
// Tables.
//
table jump_005 {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		jump_005_action
	}

	default_action jump_005_action args none const
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	table jump_005
	jmpnh LABEL_DROP
	emit h.ethernet
	tx m.port
	LABEL_DROP : drop
}
