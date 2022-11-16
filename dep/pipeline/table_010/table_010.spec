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

struct table_010_action_01_args_t {
	bit<32> ipv6_ver_tc_label
	bit<16> ipv6_payload_length
	bit<128> ipv6_dst_addr
}

//
// Actions.
//
action table_010_action_01 args instanceof table_010_action_01_args_t {
	validate h.ipv6
	mov h.ipv6.ver_tc_label t.ipv6_ver_tc_label
	mov h.ipv6.payload_length t.ipv6_payload_length
	mov h.ipv6.dst_addr t.ipv6_dst_addr
	return
}

action table_010_action_02 args none {
	mov h.ethernet.dst_addr h.ethernet.src_addr
	return
}

//
// Tables.
//
table table_010 {
	key {
		h.ipv6.dst_addr exact
	}

	actions {
		table_010_action_01
		table_010_action_02
	}

	default_action table_010_action_02 args none const
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv6
	table table_010
	emit h.ethernet
	emit h.ipv6
	tx m.port
}
