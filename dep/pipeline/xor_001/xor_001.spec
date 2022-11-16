; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2020 Intel Corporation

//
// Meta-data.
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
	xor m.port 1
	tx m.port
}
