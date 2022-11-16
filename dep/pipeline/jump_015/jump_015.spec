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

header ipv4 instanceof ipv4_h

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

header tcp instanceof tcp_h

//
// Packet meta-data.
//
struct metadata_t {
	bit<32> port
	bit<32> tcp_seq_num
	bit<16> tcp_dst_port
	bit<48> eth_src_addr
}

metadata instanceof metadata_t

//
// Actions
//
action drop args none {
    drop
}

//
// Tables.
//
table jump_015 {
	key {
	}

	actions {
		drop
	}

	default_action drop args none const
}

//
// Pipeline.
//
apply {
	rx m.port
	extract h.ethernet
	extract h.ipv4
	extract h.tcp
	mov m.tcp_seq_num h.tcp.seq_num
	mov m.tcp_dst_port h.tcp.dst_port
	mov m.eth_src_addr h.ethernet.src_addr
	jmpgt LABEL_0 m.eth_src_addr h.tcp.ack_num // >
	table jump_015
	LABEL_0 : jmpgt LABEL_1 m.tcp_seq_num h.tcp.ack_num // =
	table jump_015
	LABEL_1 : jmpgt LABEL_2 m.tcp_dst_port h.tcp.ack_num // <
	table jump_015
	LABEL_2 : emit h.ethernet
	emit h.ipv4
	emit h.tcp
	tx m.port
}
