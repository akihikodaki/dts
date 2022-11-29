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

struct vlan_h {
	bit<16> pcp_cfi_vid
	bit<16> ether_type
}

header ethernet instanceof ethernet_h
header outer_ethernet instanceof ethernet_h
header vlan instanceof vlan_h

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
struct validate_002_args_t {
	bit<48> ethernet_src_addr
}

action validate_002_action args instanceof validate_002_args_t {
	validate h.outer_ethernet
	mov h.outer_ethernet.dst_addr h.ethernet.dst_addr
	mov h.outer_ethernet.src_addr t.ethernet_src_addr
	mov h.outer_ethernet.ether_type 0x8100
	validate h.vlan
	mov h.vlan.ether_type h.ethernet.ether_type
	mov h.vlan.pcp_cfi_vid 2

	return
}

action drop args none {
	drop
}

//
// Tables.
//
table validate_002 {
	key {
		h.ethernet.ether_type exact
	}

	actions {
		validate_002_action
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
	table validate_002
	emit h.outer_ethernet
	emit h.vlan
	emit h.ethernet
	tx m.port
}
