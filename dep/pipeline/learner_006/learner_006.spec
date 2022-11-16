; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2020 Intel Corporation

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

header ethernet instanceof ethernet_h
header ipv4 instanceof ipv4_h

//
// Meta-data
//
struct metadata_t {
    bit<32> port_in
    bit<32> port_out
    bit<32> timeout_id
    bit<32> learn_006_action_01_arg
}

metadata instanceof metadata_t

//
// Actions
//
struct learn_006_action_01_args_t {
    bit<32> port_out
}

action learn_006_action_01 args instanceof learn_006_action_01_args_t {
    mov m.port_out t.port_out
    rearm
    return
}

struct learn_006_action_02_args_t {
    bit<48> src_addr
}

action learn_006_action_02 args instanceof learn_006_action_02_args_t {
    mov m.learn_006_action_01_arg m.port_in
    mov h.ethernet.src_addr t.src_addr
    mov m.timeout_id 0
    learn learn_006_action_01 m.learn_003_action_01_arg m.timeout_id
    mov m.port_out m.port_in
    return
}

//
// Tables.
//
learner learn_006 {
    key {
        h.ipv4.dst_addr
    }

    actions {
        learn_006_action_01

        learn_006_action_02
    }

    default_action learn_006_action_02 args const

    size 1048576

    timeout {
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
    table learn_006
    emit h.ethernet
    emit h.ipv4
    tx m.port_out
}