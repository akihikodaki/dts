; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2023 Intel Corporation

struct ethernet_h {
	bit<48> dst_addr
	bit<48> src_addr
	bit<16> ethertype
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

struct metadata_t {
	bit<32> port
	bit<128> swap_addr
	bit<128> temp_128
}

metadata instanceof metadata_t

apply {
	rx m.port
	extract h.ethernet
	extract h.ipv6
	mov m.swap_addr h.ipv6.src_addr
	mov m.temp_128 m.swap_addr
	mov h.ipv6.src_addr h.ipv6.dst_addr
	mov h.ipv6.dst_addr m.temp_128
	emit h.ethernet
	emit h.ipv6
	tx m.port
}