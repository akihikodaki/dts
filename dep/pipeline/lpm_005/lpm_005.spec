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

struct ipv6_h {
	bit<32> ver_tc_label
	bit<16> payload_length
	bit<8> next_header
	bit<8> hop_limit
	bit<128> src_addr
	bit<128> dst_addr
}

header ethernet instanceof ethernet_h
header ipv6 instanceof ipv6_h

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
action lpm_005_action_01 args none {
	mov h.ethernet.src_addr h.ethernet.dst_addr
	return
}

action lpm_005_action_02 args none {
	mov h.ethernet.dst_addr h.ethernet.src_addr
	return
}

//
// Tables.
//
table lpm_005 {
	key {
		h.ipv6.dst_addr lpm
	}

	actions {
		lpm_005_action_01
		lpm_005_action_02
	}

	default_action lpm_005_action_02 args none const
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv6
	table lpm_005
	emit h.ethernet
	emit h.ipv6
	tx m.port
}
