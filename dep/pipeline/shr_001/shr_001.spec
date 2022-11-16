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
// Meta-data.
//
struct metadata_t {
	bit<32> port
	bit<48> addr
	bit<8> shift
}

metadata instanceof metadata_t

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	mov m.shift 0x04
	mov m.addr h.ethernet.dst_addr
	shr m.addr m.shift
	mov h.ethernet.dst_addr m.addr
	emit h.ethernet
	tx m.port
}
