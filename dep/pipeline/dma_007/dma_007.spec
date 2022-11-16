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

struct tcp_h {
	bit<16> src_port
	bit<16> dst_port
	bit<32> seq_num
	bit<32> ack_num
	bit<16> hdr_len_flags
	bit<16> window_size
	bit<16> checksum
	bit<16> urg_ptr
}

header outer_ethernet instanceof ethernet_h
header outer_ipv4 instanceof ipv4_h
header outer_udp instanceof udp_h
header outer_vxlan instanceof vxlan_h
header ethernet instanceof ethernet_h
header ipv4 instanceof ipv4_h
header tcp instanceof tcp_h

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
struct dma_007_args_t {
	bit<48> out_ethernet_dst_addr
	bit<48> out_ethernet_src_addr
	bit<16> out_ethernet_ethertype
	bit<8> out_ipv4_ver_ihl
	bit<8> out_ipv4_diffserv
	bit<16> out_ipv4_total_len
	bit<16> out_ipv4_identification
	bit<16> out_ipv4_flags_offset
	bit<8> out_ipv4_ttl
	bit<8> out_ipv4_protocol
	bit<16> out_ipv4_hdr_checksum
	bit<32> out_ipv4_src_addr
	bit<32> out_ipv4_dst_addr
	bit<16> out_udp_src_port
	bit<16> out_udp_dst_port
	bit<16> out_udp_length
	bit<16> out_udp_checksum
	bit<8> out_vxlan_flags
	bit<24> out_vxlan_reserved
	bit<24> out_vxlan_vni
	bit<8> out_vxlan_reserved2
	bit<48> in_ethernet_dst_addr
	bit<48> in_ethernet_src_addr
	bit<16> in_ethernet_ethertype
	bit<8> in_ipv4_ver_ihl
	bit<8> in_ipv4_diffserv
	bit<16> in_ipv4_total_len
	bit<16> in_ipv4_identification
	bit<16> in_ipv4_flags_offset
	bit<8> in_ipv4_ttl
	bit<8> in_ipv4_protocol
	bit<16> in_ipv4_hdr_checksum
	bit<32> in_ipv4_src_addr
	bit<32> in_ipv4_dst_addr
	bit<16> tcp_src_port
	bit<16> tcp_dst_port
	bit<32> tcp_seq_num
	bit<32> tcp_ack_num
	bit<16> tcp_hdr_len_flags
	bit<16> tcp_window_size
	bit<16> tcp_checksum
	bit<16> tcp_urg_ptr
}

action dma_007_action args instanceof dma_007_args_t {
	mov h.outer_ethernet.dst_addr t.out_ethernet_dst_addr
	mov h.outer_ethernet.src_addr t.out_ethernet_src_addr
	mov h.outer_ethernet.ethertype t.out_ethernet_ethertype
	validate h.outer_ethernet

	mov h.outer_ipv4.ver_ihl t.out_ipv4_ver_ihl
	mov h.outer_ipv4.diffserv t.out_ipv4_diffserv
	mov h.outer_ipv4.total_len t.out_ipv4_total_len
	mov h.outer_ipv4.identification t.out_ipv4_identification
	mov h.outer_ipv4.flags_offset t.out_ipv4_flags_offset
	mov h.outer_ipv4.ttl t.out_ipv4_ttl
	mov h.outer_ipv4.protocol t.out_ipv4_protocol
	mov h.outer_ipv4.hdr_checksum t.out_ipv4_hdr_checksum
	mov h.outer_ipv4.src_addr t.out_ipv4_src_addr
	mov h.outer_ipv4.dst_addr t.out_ipv4_dst_addr
	validate h.outer_ipv4

	mov h.outer_udp.src_port t.out_udp_src_port
	mov h.outer_udp.dst_port t.out_udp_dst_port
	mov h.outer_udp.length t.out_udp_length
	mov h.outer_udp.checksum t.out_udp_checksum
	validate h.outer_udp

	mov h.outer_vxlan.flags t.out_vxlan_flags
	mov h.outer_vxlan.reserved t.out_vxlan_reserved
	mov h.outer_vxlan.vni t.out_vxlan_vni
	mov h.outer_vxlan.reserved2 t.out_vxlan_reserved2
	validate h.outer_vxlan

	mov h.ethernet.dst_addr t.in_ethernet_dst_addr
	mov h.ethernet.src_addr t.in_ethernet_src_addr
	mov h.ethernet.ethertype t.in_ethernet_ethertype
	validate h.ethernet

	mov h.ipv4.ver_ihl t.in_ipv4_ver_ihl
	mov h.ipv4.diffserv t.in_ipv4_diffserv
	mov h.ipv4.total_len t.in_ipv4_total_len
	mov h.ipv4.identification t.in_ipv4_identification
	mov h.ipv4.flags_offset t.in_ipv4_flags_offset
	mov h.ipv4.ttl t.in_ipv4_ttl
	mov h.ipv4.protocol t.in_ipv4_protocol
	mov h.ipv4.hdr_checksum t.in_ipv4_hdr_checksum
	mov h.ipv4.src_addr t.in_ipv4_src_addr
	mov h.ipv4.dst_addr t.in_ipv4_dst_addr
	validate h.ipv4

	mov h.tcp.src_port t.tcp_src_port
	mov h.tcp.dst_port t.tcp_dst_port
	mov h.tcp.seq_num t.tcp_seq_num
	mov h.tcp.ack_num t.tcp_ack_num
	mov h.tcp.hdr_len_flags t.tcp_hdr_len_flags
	mov h.tcp.window_size t.tcp_window_size
	mov h.tcp.checksum t.tcp_checksum
	mov h.tcp.urg_ptr t.tcp_urg_ptr
	validate h.tcp

	return
}

action drop args none {
	drop
}

//
// Tables.
//
table dma_007 {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		dma_007_action
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
	extract h.outer_ethernet
	extract h.outer_ipv4
	extract h.outer_udp
	extract h.outer_vxlan
	extract h.ethernet
	extract h.ipv4
	extract h.tcp
	table dma_007
	emit h.outer_ethernet
	emit h.outer_ipv4
	emit h.outer_udp
	emit h.outer_vxlan
	emit h.ethernet
	emit h.ipv4
	emit h.tcp
	tx m.port
}
