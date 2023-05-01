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
	bit<32> vrf_id
	bit<32> dst_addr
	bit<32> nexthop_group_id
	bit<32> nexthop_id
}

metadata instanceof metadata_t

//
// Actions
//
struct selector_003_action_01_args_t {
	bit<32> nexthop_group_id
}

action selector_003_action_01 args instanceof selector_003_action_01_args_t {
	mov m.nexthop_group_id t.nexthop_group_id
	return
}

struct selector_003_action_02_args_t {
	bit<48> ethernet_dst_addr
	bit<48> ethernet_src_addr
	bit<16> ethernet_ethertype
	bit<32> port_out
}

action selector_003_action_02 args instanceof selector_003_action_02_args_t {
	//Set Ethernet header.
	validate h.ethernet
	mov h.ethernet.dst_addr t.ethernet_dst_addr
	mov h.ethernet.src_addr t.ethernet_src_addr
	mov h.ethernet.ethertype t.ethernet_ethertype
	mov m.port_out t.port_out

	return
}

action drop args none {
	drop
}

//
// Tables
//
table selector_003_1_table {
	key {
		h.ipv4.dst_addr exact
	}

	actions {
		selector_003_action_01
		drop
	}

	default_action drop args none

	size 1048576
}

selector selector_003_2_table {
	group_id m.nexthop_group_id

	selector {
		h.ipv4.protocol
		h.ipv4.src_addr
		h.ipv4.dst_addr
	}

	member_id m.nexthop_id

	n_groups_max 6553

	n_members_per_group_max 80
}

table selector_003_3_table {
	key {
		m.nexthop_id exact
	}

	actions {
		selector_003_action_02
		drop
	}

	default_action drop args none

	size 1048576
}

//
// Pipeline
//
apply {
	rx m.port_in
	extract h.ethernet
	extract h.ipv4
	table selector_003_1_table
	table selector_003_2_table
	table selector_003_3_table
	emit h.ethernet
	emit h.ipv4
	tx m.port_out
}
