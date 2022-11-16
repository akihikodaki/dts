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

header outer_ethernet instanceof ethernet_h
header ethernet instanceof ethernet_h

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

header outer_ipv4 instanceof ipv4_h
header ipv4 instanceof ipv4_h

struct udp_h {
	bit<16> src_port
	bit<16> dst_port
	bit<16> length
	bit<16> checksum
}

header outer_udp instanceof udp_h

struct vxlan_h {
	bit<8> flags
	bit<24> reserved
	bit<24> vni
	bit<8> reserved2
}

header outer_vxlan instanceof vxlan_h

//
// Packet meta-data.
//
struct metadata_t {
	bit<32> port
}

metadata instanceof metadata_t

//
// Pipeline.
//
apply {
	rx m.port
	extract h.outer_ethernet
	extract h.outer_ipv4
	extract h.outer_udp
	extract h.outer_vxlan
	extract h.ethernet
	extract h.ipv4
	emit h.outer_ethernet
	emit h.outer_ipv4
	emit h.outer_udp
	emit h.outer_vxlan
	emit h.ethernet
	emit h.ipv4
	tx m.port
}
