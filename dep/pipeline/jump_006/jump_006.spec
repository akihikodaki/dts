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
action jump_006_action_01 args none {
	return
}

action jump_006_action_02 args none {
	return
}

action drop args none {
	drop
}

//
// Tables.
//
table jump_006 {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		jump_006_action_01
		jump_006_action_02
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
	table jump_006
	jmpa LABEL_0 jump_006_action_01
	jmp LABEL_DROP
	LABEL_0 : emit h.ethernet
	tx m.port
	LABEL_DROP : drop
}
