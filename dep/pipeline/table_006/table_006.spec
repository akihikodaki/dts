; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2010-2020 Intel Corporation

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

struct udp_h {
	bit<16> src_port
	bit<16> dst_port
	bit<16> length
	bit<16> checksum
}

struct vxlan_h {
	bit<8> flags
	bit<24> reserved
	bit<24> vni
	bit<8> reserved2
}

header ethernet instanceof ethernet_h
header ipv4 instanceof ipv4_h
header outer_ethernet instanceof ethernet_h
header outer_ipv4 instanceof ipv4_h
header outer_udp instanceof udp_h
header outer_vxlan instanceof vxlan_h

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
struct table_006_args_t {
	bit<48> ethernet_src_addr
}

action table_006_action_01 args instanceof table_006_args_t {
	mov h.ethernet.src_addr t.ethernet_src_addr
	mov m.port_out m.port_in
	return
}

//
// Actions
//
struct vxlan_encap_args_t {
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
	bit<16> udp_src_port
	bit<16> udp_dst_port
	bit<16> udp_length
	bit<16> udp_checksum
	bit<8> vxlan_flags
	bit<24> vxlan_reserved
	bit<24> vxlan_vni
	bit<8> vxlan_reserved2
	bit<32> port_out
}

action table_006_default_action_01 args instanceof vxlan_encap_args_t {
	//Set the outer Ethernet header.
	validate h.outer_ethernet
	mov h.outer_ethernet.dst_addr t.ethernet_dst_addr
	mov h.outer_ethernet.src_addr t.ethernet_src_addr
	mov h.outer_ethernet.ethertype t.ethernet_ethertype

	//Set the outer IPv4 header.
	validate h.outer_ipv4
	mov h.outer_ipv4.ver_ihl t.ipv4_ver_ihl
	mov h.outer_ipv4.diffserv t.ipv4_diffserv
	mov h.outer_ipv4.total_len t.ipv4_total_len
	mov h.outer_ipv4.identification t.ipv4_identification
	mov h.outer_ipv4.flags_offset t.ipv4_flags_offset
	mov h.outer_ipv4.ttl t.ipv4_ttl
	mov h.outer_ipv4.protocol t.ipv4_protocol
	mov h.outer_ipv4.hdr_checksum t.ipv4_hdr_checksum
	mov h.outer_ipv4.src_addr t.ipv4_src_addr
	mov h.outer_ipv4.dst_addr t.ipv4_dst_addr

	//Set the outer UDP header.
	validate h.outer_udp
	mov h.outer_udp.src_port t.udp_src_port
	mov h.outer_udp.dst_port t.udp_dst_port
	mov h.outer_udp.length t.udp_length
	mov h.outer_udp.checksum t.udp_checksum

	//Set the outer VXLAN header.
	validate h.outer_vxlan
	mov h.outer_vxlan.flags t.vxlan_flags
	mov h.outer_vxlan.reserved t.vxlan_reserved
	mov h.outer_vxlan.vni t.vxlan_vni
	mov h.outer_vxlan.reserved2 t.vxlan_reserved2

	//Set the output port.
	mov m.port_out t.port_out

	//Update h.outer_ipv4.total_len field.
	add h.outer_ipv4.total_len h.ipv4.total_len

	//Update h.outer_ipv4.hdr_checksum field.
	ckadd h.outer_ipv4.hdr_checksum h.ipv4.total_len

	//Update h.outer_udp.length field.
	add h.outer_udp.length h.ipv4.total_len

	return
}

//
// Tables.
//
table table_006_table {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		table_006_action_01
		table_006_default_action_01
	}

	default_action table_006_default_action_01 args ethernet_dst_addr 0xa0a1a2a30000 ethernet_src_addr 0xb0b1b2b30000 ethernet_ethertype 0x0800 ipv4_ver_ihl 0x45 ipv4_diffserv 0 ipv4_total_len 50 ipv4_identification 0 ipv4_flags_offset 0 ipv4_ttl 64 ipv4_protocol 17 ipv4_hdr_checksum 0xe928 ipv4_src_addr 0xc0c10000 ipv4_dst_addr 0xd0d10000 udp_src_port 0xe000 udp_dst_port 4789 udp_length 30 udp_checksum 0 vxlan_flags 0 vxlan_reserved 0 vxlan_vni 0 vxlan_reserved2 0 port_out 0
	size 1048576
}

//
// Pipeline.
//
apply {
	rx m.port_in
	extract h.ethernet
	extract h.ipv4
	table table_006_table
	emit h.outer_ethernet
	emit h.outer_ipv4
	emit h.outer_udp
	emit h.outer_vxlan
	emit h.ethernet
	emit h.ipv4
	tx m.port_out
}
