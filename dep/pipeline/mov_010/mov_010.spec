; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2023 Intel Corporation

struct ethernet_h {
	bit<48> dst_addr
	bit<48> src_addr
	bit<16> ethertype
}

struct ipv4_h {
	bit<64> ver_ihl_diffserv_len_id_flags
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
	bit<128> swap_addr
	bit<128> temp_128
	bit<128> temp_128_64
	bit<128> temp_128_8
}

metadata instanceof metadata_t

action mov_010_action_01 args none {
	mov h.ipv6.dst_addr h.ipv4.src_addr
	mov h.ipv6.src_addr h.ipv6.payload_length
	return
}

action mov_010_action_02 args none {
	mov h.ipv6.src_addr h.ethernet.src_addr
	return
}

action mov_010_action_03 args none {
	mov h.ipv6.src_addr h.ipv4.ver_ihl_diffserv_len_id_flags
	mov h.ipv6.dst_addr h.ipv4.ttl
	return
}

action mov_010_action_04 args none {
	mov m.temp_128_64 h.ipv4.ver_ihl_diffserv_len_id_flags
	mov m.temp_128_8 h.ipv4.ttl
	mov h.ipv6.src_addr m.temp_128_64
	mov h.ipv6.dst_addr m.temp_128_8
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
		mov_010_action_01
		mov_010_action_02
		mov_010_action_03
		mov_010_action_04
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
