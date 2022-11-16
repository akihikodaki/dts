; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2022 Intel Corporation

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

struct tcp_t {
    bit<16> srcPort
    bit<16> dstPort
    bit<32> seqNo
    bit<32> ackNo
    bit<8> dataOffset_res
    bit<8> flags
    bit<16> window
    bit<16> checksum
    bit<16> urgentPtr
}

header ethernet instanceof ethernet_h
header ipv4 instanceof ipv4_h
header tcp instanceof tcp_t

//
// Meta-data
//
struct metadata_t {
    bit<8> timeout_id
    bit<32> port_out
    bit<32> port_in
    bit<8> ipv4_protocol
    bit<32> ipv4_dst_addr
    bit<16> tcp_src_port
    bit<16> tcp_dst_port
    bit<32> ipv4_src_addr
    bit<32> learn_011_action_01_arg
}

metadata instanceof metadata_t

//
// Actions
//
struct learn_011_action_01_args_t {
    bit<32> port_out
}

action learn_011_action_01 args instanceof learn_011_action_01_args_t {
    mov m.port_out t.port_out
    mov m.timeout_id 2
    rearm m.timeout_id
    return
}

action learn_011_action_02 args none {
    mov m.port_out 0
    mov m.learn_011_action_01_arg 1
    mov m.timeout_id 0
    learn learn_011_action_01 m.learn_011_action_01_arg m.timeout_id
    return
}

//
// Tables.
//
learner learn_011 {
    key {
        m.ipv4_src_addr
        m.ipv4_dst_addr
        m.ipv4_protocol
        m.tcp_src_port
        m.tcp_dst_port
    }

    actions {
        learn_011_action_01

        learn_011_action_02
    }

    default_action learn_011_action_02 args none

    size 1048576

    timeout {
        30
        60
        120
        120
        120
        120
        120
        120
    }
}

//
// Pipeline.
//
apply {
    rx m.port_in
    extract h.ethernet
    extract h.ipv4
    extract h.tcp
    mov m.ipv4_src_addr h.ipv4.src_addr
    mov m.ipv4_dst_addr h.ipv4.dst_addr
    mov m.ipv4_protocol h.ipv4.protocol
    mov m.tcp_src_port h.tcp.srcPort
    mov m.tcp_dst_port h.tcp.dstPort
    table learn_011
    emit h.ethernet
    emit h.ipv4
    emit h.tcp
    tx m.port_out
}
