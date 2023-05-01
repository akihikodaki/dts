; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2020 Intel Corporation

//
// Packet headers.
//
struct ethernet_h {
	bit<48> dst_addr
	bit<48> src_addr
}

struct vlan_h {
	bit<16> tpid
	bit<16> pcp_dei_vid
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

header ethernet instanceof ethernet_h
header vlan instanceof vlan_h
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
struct dma_004_args_t {
	bit<48> ethernet_dst_addr
	bit<48> ethernet_src_addr
	bit<16> vlan_tpid
	bit<16> vlan_pcp_dei_vid
	bit<16> vlan_ethertype
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
	bit<16> tcp_src_port
	bit<16> tcp_dst_port
	bit<32> tcp_seq_num
	bit<32> tcp_ack_num
	bit<16> tcp_hdr_len_flags
	bit<16> tcp_window_size
	bit<16> tcp_checksum
	bit<16> tcp_urg_ptr
}

action dma_004_action args instanceof dma_004_args_t {
	validate h.ethernet
	mov h.ethernet.dst_addr t.ethernet_dst_addr
	mov h.ethernet.src_addr t.ethernet_src_addr

	validate h.vlan
	mov h.vlan.tpid t.vlan_tpid
	mov h.vlan.pcp_dei_vid t.vlan_pcp_dei_vid
	mov h.vlan.ethertype t.vlan_ethertype

	validate h.ipv4
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

	validate h.tcp
	mov h.tcp.src_port t.tcp_src_port
	mov h.tcp.dst_port t.tcp_dst_port
	mov h.tcp.seq_num t.tcp_seq_num
	mov h.tcp.ack_num t.tcp_ack_num
	mov h.tcp.hdr_len_flags t.tcp_hdr_len_flags
	mov h.tcp.window_size t.tcp_window_size
	mov h.tcp.checksum t.tcp_checksum
	mov h.tcp.urg_ptr t.tcp_urg_ptr

	return
}

action drop args none {
	drop
}

//
// Tables.
//
table dma_004 {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		dma_004_action
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
	extract h.vlan
	extract h.ipv4
	extract h.tcp
	table dma_004
	emit h.ethernet
	emit h.vlan
	emit h.ipv4
	emit h.tcp
	tx m.port
}
