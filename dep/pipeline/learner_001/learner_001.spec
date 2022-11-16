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
    bit<32> learn_001_action_01_arg
}

metadata instanceof metadata_t

//
// Actions
//
struct learn_001_action_01_args_t {
    bit<32> port_out
}

action learn_001_action_01 args instanceof learn_001_action_01_args_t {
    mov m.port_out t.port_out
    rearm
    return
}

action learn_001_action_02 args none {
    mov m.learn_001_action_01_arg m.port_in
    mov m.timeout_id 0
    learn learn_001_action_01 m.learn_001_action_01_arg m.timeout_id
    return
}

//
// Tables.
//
learner learn_001 {
    key {
        h.ipv4.dst_addr
    }

    actions {
        learn_001_action_01

        learn_001_action_02
    }

    default_action learn_001_action_02 args none

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
    table learn_001
    jmpa DROP learn_001_action_02
    emit h.ethernet
    emit h.ipv4
    tx m.port_out
    DROP : drop
}