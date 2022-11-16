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

struct table_011_action_01_args_t {
	bit<32> ipv6_ver_tc_label
	bit<16> ipv6_payload_length
	bit<8> ipv6_next_header
	bit<8> ipv6_hop_limit
	bit<128> ipv6_src_addr
	bit<128> ipv6_dst_addr
}

//
// Actions.
//
action table_011_action_01 args instanceof table_011_action_01_args_t {
	//Set the IPv6 header.
	validate h.ipv6

	mov h.ipv6.ver_tc_label t.ipv6_ver_tc_label
	mov h.ipv6.payload_length t.ipv6_payload_length
	mov h.ipv6.next_header t.ipv6_next_header
	mov h.ipv6.hop_limit t.ipv6_hop_limit
	mov h.ipv6.src_addr t.ipv6_src_addr
	mov h.ipv6.dst_addr t.ipv6_dst_addr

	return
}

action table_011_action_02 args none {
	mov h.ethernet.dst_addr h.ethernet.src_addr
	return
}

//
// Tables.
//
table table_011 {
	key {
		h.ipv6.dst_addr exact
	}

	actions {
		table_011_action_01
		table_011_action_02
	}

	default_action table_011_action_01 args ipv6_ver_tc_label 0x60000000 ipv6_payload_length 70 ipv6_next_header 17 ipv6_hop_limit 64 ipv6_src_addr 0xa0a1a2a3a4a5a6a7a8a9aaabacadaeaf ipv6_dst_addr 0xb0b1b2b3b4b5b6b7b8b9babbbcbdbebf
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv6
	table table_011
	emit h.ethernet
	emit h.ipv6
	tx m.port
}
