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

struct ipv4_h {
	bit<8> ver_ihl
	bit<8> diffserv
	bit<80> len_id_flags_tt_protocol_checksum
	bit<32> src_addr
	bit<32> dst_addr
}
header ethernet instanceof ethernet_h
header ipv4 instanceof ipv4_h

//
// Packet meta-data.
//
struct metadata_t {
	bit<32> port
	bit<64> temp_64
	bit<80> temp_80
}

metadata instanceof metadata_t

struct table_012_action_01_args_t {
	bit<80> ipv4_len_id_flags_tt_protocol_checksum
}

//
// Actions.
//
action table_012_action_01 args instanceof table_012_action_01_args_t {
	validate h.ipv4
	mov h.ipv4.len_id_flags_tt_protocol_checksum t.ipv4_len_id_flags_tt_protocol_checksum
	return
}

action table_012_action_02 args none {
	mov h.ethernet.dst_addr h.ethernet.src_addr
	return
}

//
// Tables.
//
table table_012 {
	key {
		h.ipv4.len_id_flags_tt_protocol_checksum exact
	}

	actions {
		table_012_action_01
		table_012_action_02
	}

	default_action table_012_action_02 args none const
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4
	table table_012
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
