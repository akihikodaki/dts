; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2020 Intel Corporation

//
// Packet headers.
//
struct ethernet_1_h {
    bit<48> dst_addr
    bit<48> src_addr
    bit<16> ether_type
}

header outer_ethernet instanceof ethernet_1_h

struct ethernet_2_h {
    bit<48> dst_addr
    bit<48> src_addr
    bit<16> ether_type
}

header ethernet instanceof ethernet_2_h

struct vlan_h {
    bit<16> tpid
    bit<16> ether_type
}

header vlan instanceof vlan_h
header vlan_1 instanceof vlan_h
header vlan_2 instanceof vlan_h
header vlan_3 instanceof vlan_h

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
    extract h.vlan
    extract h.vlan_1
    extract h.vlan_2
    extract h.vlan_3
    extract h.ipv4
    extract h.tcp

    invalidate h.outer_ethernet
    invalidate h.outer_ipv4
    invalidate h.outer_udp
    invalidate h.outer_vxlan
    invalidate h.ethernet
    invalidate h.vlan
    invalidate h.vlan_1
    invalidate h.vlan_2
    invalidate h.vlan_3
    invalidate h.ipv4
    invalidate h.tcp


    emit h.outer_ethernet
    emit h.outer_ipv4
    emit h.outer_udp
    emit h.outer_vxlan
    emit h.ethernet
    emit h.vlan
    emit h.vlan_1
    emit h.vlan_2
    emit h.vlan_3
    emit h.ipv4
    emit h.tcp
    tx m.port
}
