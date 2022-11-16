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

// IPv4 Header
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

// UDP Header
struct udp_h {
	bit<16> src_port
	bit<16> dst_port
	bit<16> length
	bit<16> checksum
}

// VXLAN Header
struct vxlan_h {
	bit<8> flags
	bit<24> reserved
	bit<24> vni
	bit<8> reserved2
}

// Header instances
header outer_ethernet instanceof ethernet_h
header outer_ipv4 instanceof ipv4_h
header outer_udp instanceof udp_h
header vxlan instanceof vxlan_h
header inner_ethernet instanceof ethernet_h
header inner_ipv4 instanceof ipv4_h
header inner_udp instanceof udp_h


//
// Packet meta-data.
//

struct metadata_t {
	bit<32> port
	bit<32> outer_ipv4_src_addr
	bit<32> outer_ipv4_dst_addr
	bit<16> outer_udp_src_port
	bit<16> outer_udp_dst_port
	bit<24> vni
	bit<8> protocol
	bit<32> inner_ipv4_src_addr
	bit<32> inner_ipv4_dst_addr
	bit<16> inner_udp_src_port
	bit<16> inner_udp_dst_port
}

metadata instanceof metadata_t

struct table_015_action_01_args_t {
	bit<24> t_vni
}

// Action 01: Update field in the header data
action table_015_action_01 args instanceof table_015_action_01_args_t {
	mov h.vxlan.vni t.t_vni
	return
}

// Action 02: Decapsulation
action table_015_action_02 args none {
	invalidate h.outer_ethernet
	invalidate h.outer_ipv4
	invalidate h.outer_udp
	invalidate h.vxlan
	return
}

table table_015 {

	key {
		m.outer_ipv4_src_addr exact
		m.outer_ipv4_dst_addr exact
		m.outer_udp_src_port exact
		m.outer_udp_dst_port exact
		m.vni exact
		m.protocol exact
		m.inner_ipv4_src_addr exact
		m.inner_ipv4_dst_addr exact
		m.inner_udp_src_port exact
		m.inner_udp_dst_port exact
	}

	actions {
		table_015_action_01
		table_015_action_02
	}

	default_action table_015_action_02 args none const
	size 1048576
}

apply {
	// Receive packet
	rx m.port
	extract h.outer_ethernet
	// Verify if packets are arrived in correct
	// order. If not, go to END.
	// Ethernet -> IPv4 -> UDP -> VXLAN ->
	// Ethernet -> IPv4 -> UDP
	jmpneq END h.outer_ethernet.ether_type 0x0800
	extract h.outer_ipv4
	jmpneq END h.outer_ipv4.protocol 0x11
	extract h.outer_udp
	jmpneq END h.outer_udp.dst_port 4789
	extract h.vxlan
	extract h.inner_ethernet
	jmpneq END h.inner_ethernet.ether_type 0x0800
	extract h.inner_ipv4
	jmpneq END h.inner_ipv4.protocol 0x11
	extract h.inner_udp

	// Copy the required key data fields from header
	// into the metadata key fields.
	mov m.outer_ipv4_src_addr h.outer_ipv4.src_addr
	mov m.outer_ipv4_dst_addr h.outer_ipv4.dst_addr
	mov m.outer_udp_src_port h.outer_udp.src_port
	mov m.outer_udp_dst_port h.outer_udp.dst_port
	mov m.vni h.vxlan.vni
	mov m.protocol h.inner_ipv4.protocol
	mov m.inner_ipv4_src_addr h.inner_ipv4.src_addr
	mov m.inner_ipv4_dst_addr h.inner_ipv4.dst_addr
	mov m.inner_udp_src_port h.inner_udp.src_port
	mov m.inner_udp_dst_port h.inner_udp.dst_port

	// Table operations
	table table_015

	// Transmit packets
	END : emit h.outer_ethernet
	emit h.outer_ipv4
	emit h.outer_udp
	emit h.vxlan
	emit h.inner_ethernet
	emit h.inner_ipv4
	emit h.inner_udp
	tx m.port
}
