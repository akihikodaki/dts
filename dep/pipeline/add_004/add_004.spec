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
    bit<16> total_len
    bit<16> identification
    bit<16> flags_offset
    bit<8> ttl
    bit<8> protocol
    bit<16> hdr_checksum
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
    bit<48> eth_src_addr
	bit<32> ip_src_addr
	bit<32> ip_dst_addr
}

metadata instanceof metadata_t

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
    extract h.ipv4
    mov m.eth_src_addr h.ethernet.src_addr
    mov m.ip_src_addr h.ipv4.src_addr
	mov m.ip_dst_addr h.ipv4.dst_addr
	add m.ip_dst_addr h.ethernet.src_addr
	add m.eth_src_addr h.ethernet.dst_addr
	add m.ip_src_addr h.ipv4.hdr_checksum
	mov h.ipv4.dst_addr m.ip_dst_addr
	mov h.ethernet.src_addr m.eth_src_addr
	mov h.ipv4.src_addr m.ip_src_addr
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
