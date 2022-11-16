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
	bit<48> addr
}

metadata instanceof metadata_t

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	xor h.ethernet.dst_addr h.ethernet.src_addr
	emit h.ethernet
	tx m.port
}
