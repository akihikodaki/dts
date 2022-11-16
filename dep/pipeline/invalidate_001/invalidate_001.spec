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
action drop args none {
    drop
}

//
// Tables.
//
table invalidate_001 {
	key {
	}

	actions {
		drop
	}

	default_action drop args none const
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	jmpeq LABEL_0 h.ethernet.ether_type 0x0800
	invalidate h.ethernet
	LABEL_0 : jmpv LABEL_1 h.ethernet
	table invalidate_001
	LABEL_1 : emit h.ethernet
	tx m.port
}
