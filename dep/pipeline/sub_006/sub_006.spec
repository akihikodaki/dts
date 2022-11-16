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
	bit<48> addr_1
	bit<48> addr_2
}

metadata instanceof metadata_t

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	mov m.addr_1 h.ethernet.src_addr
	mov m.addr_2 h.ethernet.dst_addr
	sub m.addr_2 m.addr_1
	mov h.ethernet.dst_addr m.addr_2
	emit h.ethernet
	tx m.port
}
