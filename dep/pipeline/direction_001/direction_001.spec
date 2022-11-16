; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2022 Intel Corporation

; This simple example illustrates that the ports can be configured into two different direction,
; HOST_TO_NETWORK and NETWORK_TO_HOST. This helps to apply different functions (processing) for
; packets from different direction.
; In this example, different L2/MAC address are updated based on the configured direction.

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

struct udp_h {
	bit<16> src_port
	bit<16> dst_port
	bit<16> length
	bit<16> checksum
}

header ethernet instanceof ethernet_h
header ipv4 instanceof ipv4_h
header udp instanceof udp_h

//
// Meta-data.
//
struct metadata_t {
	bit<32> input_port
	bit<32> direction
}

metadata instanceof metadata_t

//
// register to hold the direction of the port
//
regarray direction size 0x100 initval 0

//
// Pipeline.
//
apply {
	rx m.input_port
	extract h.ethernet
	extract h.ipv4
	extract h.udp

	//
	// Update the source and destination mac address based on direction
	//
	regrd m.direction direction m.input_port
	jmpneq PACKET_FROM_HOST m.direction 0x0
	mov h.ethernet.dst_addr 0x001122334455
	mov h.ethernet.src_addr 0x00AABBCCDDEE
	jmp EMIT
	PACKET_FROM_HOST : mov h.ethernet.dst_addr 0x00EEDDCCBBAA
	mov h.ethernet.src_addr 0x005544332211

	EMIT : emit h.ethernet
	emit h.ipv4
	emit h.udp
	tx m.input_port
}
