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
        extract h.ethernet
        jmp LABEL_0
        mov h.ethernet.dst_addr 0xa0b0c0d00000
        LABEL_0 : emit h.ethernet
        tx m.port
 }