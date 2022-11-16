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

header ethernet instanceof ethernet_h
header ipv4 instanceof ipv4_h

//
// Meta-data
//
struct metadata_t {
    bit<32> port_in
    bit<32> port_out
    bit<32> timeout_id
    bit<32> learn_009_action_01_arg
}

metadata instanceof metadata_t

//
// Actions
//
struct learn_009_action_01_args_t {
    bit<32> port_out
}

action learn_009_action_01 args instanceof learn_009_action_01_args_t {
    mov m.port_out t.port_out
    return
}

action learn_009_action_02 args none {
    mov m.port_out 0
    mov m.learn_009_action_01_arg 1
    mov m.timeout_id 1
    learn learn_009_action_01 m.learn_009_action_01_arg m.timeout_id
    return
}

//
// Tables.
//
learner learn_009 {
    key {
        h.ipv4.dst_addr
    }

    actions {
        learn_009_action_01

        learn_009_action_02
    }

    default_action learn_009_action_02 args none

    size 1048576

    timeout {
        30
        60
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
    table learn_009
    emit h.ethernet
    emit h.ipv4
    tx m.port_out
}