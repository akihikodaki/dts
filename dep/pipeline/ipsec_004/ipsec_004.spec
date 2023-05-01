; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2020 Intel Corporation

;
//
// Headers
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

struct ipsec_internal_h {
	bit<32> sa_id
}

header ethernet instanceof ethernet_h
header ipv4 instanceof ipv4_h
header ipsec_internal instanceof ipsec_internal_h

//
// Meta-data
//
struct metadata_t {
	bit<32> port_in
	bit<32> port_out
}

metadata instanceof metadata_t

//
// Actions
//
struct encrypt_args_t {
	bit<32> sa_id
}

action encrypt args instanceof encrypt_args_t {
	//Set the IPsec internal header.
	validate h.ipsec_internal
	mov h.ipsec_internal.sa_id t.sa_id
	mov m.port_out 1
	invalidate h.ethernet
	return
}

action drop args none {
	drop
}

//
// Tables.
//
table policy_table {
	key {
		h.ipv4.src_addr exact
		h.ipv4.dst_addr exact
		h.ipv4.protocol exact
	}

	actions {
		encrypt
		drop
	}

	default_action drop args none
	size 65536
}

//
// Pipeline.
//
apply {
	rx m.port_in
	jmpeq FROM_IPSEC m.port_in 1
	extract h.ethernet
	extract h.ipv4
	table policy_table
	jmp SEND_PACKET

FROM_IPSEC : extract h.ipv4
	jmpneq SEND_IPSEC_TO_NET h.ipv4.protocol 0x32
	table policy_table
	jmp SEND_PACKET

SEND_IPSEC_TO_NET : validate h.ethernet
	mov h.ethernet.dst_addr 0x000102030405
	mov h.ethernet.src_addr 0x000a0b0c0d0e
	mov h.ethernet.ethertype 0x0800
	mov m.port_out 0

SEND_PACKET : emit h.ipsec_internal
	emit h.ethernet
	emit h.ipv4
	tx m.port_out
}
