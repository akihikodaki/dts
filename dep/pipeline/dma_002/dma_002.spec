; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2020 Intel Corporation

//
// Packet headers.
//
struct ethernet_h {
	bit<48> dst_addr
	bit<48> src_addr
	bit<16> ethertype
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
}

metadata instanceof metadata_t

//
// Actions
//
struct dma_002_args_t {
	bit<48> ethernet_dst_addr
	bit<48> ethernet_src_addr
	bit<16> ethernet_ethertype
	bit<8> ipv4_ver_ihl
	bit<8> ipv4_diffserv
	bit<16> ipv4_total_len
	bit<16> ipv4_identification
	bit<16> ipv4_flags_offset
	bit<8> ipv4_ttl
	bit<8> ipv4_protocol
	bit<16> ipv4_hdr_checksum
	bit<32> ipv4_src_addr
	bit<32> ipv4_dst_addr
}

action dma_002_action args instanceof dma_002_args_t {
	mov h.ethernet.dst_addr t.ethernet_dst_addr
	mov h.ethernet.src_addr t.ethernet_src_addr
	mov h.ethernet.ethertype t.ethernet_ethertype
	validate h.ethernet

	mov h.ipv4.ver_ihl t.ipv4_ver_ihl
	mov h.ipv4.diffserv t.ipv4_diffserv
	mov h.ipv4.total_len t.ipv4_total_len
	mov h.ipv4.identification t.ipv4_identification
	mov h.ipv4.flags_offset t.ipv4_flags_offset
	mov h.ipv4.ttl t.ipv4_ttl
	mov h.ipv4.protocol t.ipv4_protocol
	mov h.ipv4.hdr_checksum t.ipv4_hdr_checksum
	mov h.ipv4.src_addr t.ipv4_src_addr
	mov h.ipv4.dst_addr t.ipv4_dst_addr
	validate h.ipv4

	return
}

action drop args none {
	drop
}

//
// Tables.
//
table dma_002 {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		dma_002_action
		drop
	}

	default_action drop args none
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4
	table dma_002
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
