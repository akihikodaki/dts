; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2023 Intel Corporation

struct ethernet_h {
	bit<96> dst_src_addr
	bit<16> ethertype
}

struct ipv4_h {
	bit<16> ver_ihl_diffserv
	bit<48> total_len_identification_flags
	bit<8> ttl
	bit<8> protocol
	bit<16> hdr_checksum
	bit<32> src_addr
	bit<32> dst_addr
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
header ipv4 instanceof ipv4_h
header ipv6 instanceof ipv6_h

struct metadata_t {
	bit<32> port
	bit<128> temp_128
}

metadata instanceof metadata_t

action mov_012_action_01 args none {
	mov h.ipv4.src_addr h.ipv6.dst_addr
	mov h.ipv4.total_len_identification_flags h.ipv6.src_addr
	return
}

action mov_012_action_02 args none {
	mov m.temp_128 h.ipv6.src_addr
	mov h.ethernet.dst_src_addr m.temp_128
	return
}

action drop args none {
	drop
	return
}

table table_001 {

	key {
		h.ipv4.src_addr exact
	}

	actions {
		mov_012_action_01
		mov_012_action_02
		drop
	}

	default_action drop args none const
	size 1048576
}

apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4
	extract h.ipv6
	table table_001
	emit h.ethernet
	emit h.ipv4
	emit h.ipv6
	tx m.port
}