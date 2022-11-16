; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2010-2020 Intel Corporation

//
// Headers
//
struct ethernet_h {
	bit<48> dst_addr
	bit<48> src_addr
	bit<16> ethertype
}

header ethernet instanceof ethernet_h

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
struct dma_001_args_t {
	bit<48> ethernet_dst_addr
	bit<48> ethernet_src_addr
	bit<16> ethernet_ethertype
}

action dma_001_action args instanceof dma_001_args_t {
	mov h.ethernet.dst_addr t.ethernet_dst_addr
	mov h.ethernet.src_addr t.ethernet_src_addr
	mov h.ethernet.ethertype t.ethernet_ethertype
	validate h.ethernet
	return
}

action drop args none {
	drop
}

//
// Tables.
//
table dma_001 {
	key {
		h.ethernet.dst_addr exact
	}

	actions {
		dma_001_action
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
	table dma_001
	emit h.ethernet
	tx m.port
}
