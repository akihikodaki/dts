;SPDX-License-Identifier: BSD-3-Clause
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
header ipv4 instanceof ipv4_h
header tcp instanceof tcp_h

//
// Meta-data
//
struct metadata_t {
        bit<32> port
}

metadata instanceof metadata_t

//
// Actions
//
struct jump_031_args_t {
        bit<32> ip_dst_addr
}

action jump_031_action args instanceof jump_031_args_t {
    jmpeq LABEL_0 t.ip_dst_addr 0xc800000a
	mov m.port 4
	LABEL_0 : sub h.ipv4.ttl 1
    return
}

action drop args none {
    drop
}

//
//table
//
table jump_031_table {
        key {
             h.tcp.dst_port exact
        }

        actions {
                jump_031_action
                drop
        }

        default_action drop args none
        size 1048576
}

//
// Pipeline
//
apply {
        rx m.port
        extract h.ethernet
	extract h.ipv4
	extract h.tcp
        table jump_031_table
        emit h.ethernet
	emit h.ipv4
	emit h.tcp
        tx m.port
}
