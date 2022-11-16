struct ethernet_h {
	bit<48> dst_addr
	bit<48> src_addr
	bit<16> ether_type
}

struct ipv4_h {
	bit<8> version_ihl
	bit<8> diffserv
	bit<16> total_len
	bit<16> identification
	bit<16> flags_frag_offset
	bit<8> ttl
	bit<8> protocol
	bit<16> hdr_checksum
	bit<32> src_addr
	bit<32> dst_addr
}

struct ipv6_h {
	bit<32> version_traffic_class_flow_label
	bit<16> payload_len
	bit<8> next_hdr
	bit<8> hop_limit
	bit<64> src_addr_hi
	bit<64> src_addr_lo
	bit<64> dst_addr_hi
	bit<64> dst_addr_lo
}

struct icmp_h {
	bit<16> type_code
	bit<16> checksum
}

struct igmp_h {
	bit<16> type_code
	bit<16> checksum
}

struct tcp_h {
	bit<16> src_port
	bit<16> dst_port
	bit<32> seq_no
	bit<32> ack_no
	bit<8> data_offset_res
	bit<8> flags
	bit<16> window
	bit<16> checksum
	bit<16> urgent_ptr
}

struct udp_h {
	bit<16> src_port
	bit<16> dst_port
	bit<16> len
	bit<16> checksum
}

struct cksum_state_t {
	bit<16> state_0
}

struct vlan_tag_h {
	bit<16> pcp_cfi_vid
	bit<16> ether_type
}

struct l3_switch_arg_t {
	bit<32> port
	bit<48> new_mac_da
	bit<48> new_mac_sa
}

struct nexthop_1_set_group_id_arg_t {
	bit<32> group_id
}

struct send_arg_t {
	bit<32> port
}

struct set_nexthop_arg_t {
	bit<16> nexthop
}

header ethernet instanceof ethernet_h
header vlan_tag_0 instanceof vlan_tag_h
header vlan_tag_1 instanceof vlan_tag_h

header ipv4 instanceof ipv4_h
header ipv6 instanceof ipv6_h
header icmp instanceof icmp_h
header igmp instanceof igmp_h
header tcp instanceof tcp_h
header udp instanceof udp_h
header cksum_state instanceof cksum_state_t

struct my_ingress_metadata_t {
	bit<32> psa_ingress_parser_input_metadata_ingress_port
	bit<32> psa_ingress_parser_input_metadata_packet_path
	bit<32> psa_egress_parser_input_metadata_egress_port
	bit<32> psa_egress_parser_input_metadata_packet_path
	bit<32> psa_ingress_input_metadata_ingress_port
	bit<32> psa_ingress_input_metadata_packet_path
	bit<64> psa_ingress_input_metadata_ingress_timestamp
	bit<8> psa_ingress_input_metadata_parser_error
	bit<8> psa_ingress_output_metadata_class_of_service
	bit<8> psa_ingress_output_metadata_clone
	bit<16> psa_ingress_output_metadata_clone_session_id
	bit<8> psa_ingress_output_metadata_drop
	bit<8> psa_ingress_output_metadata_resubmit
	bit<32> psa_ingress_output_metadata_multicast_group
	bit<32> psa_ingress_output_metadata_egress_port
	bit<8> psa_egress_input_metadata_class_of_service
	bit<32> psa_egress_input_metadata_egress_port
	bit<32> psa_egress_input_metadata_packet_path
	bit<16> psa_egress_input_metadata_instance
	bit<64> psa_egress_input_metadata_egress_timestamp
	bit<8> psa_egress_input_metadata_parser_error
	bit<32> psa_egress_deparser_input_metadata_egress_port
	bit<8> psa_egress_output_metadata_clone
	bit<16> psa_egress_output_metadata_clone_session_id
	bit<8> psa_egress_output_metadata_drop
	bit<32> local_metadata__l4_lookup_ipv4_src_addr0
	bit<32> local_metadata__l4_lookup_ipv4_dst_addr1
	bit<8> local_metadata__l4_lookup_ipv4_protocol2
	bit<16> local_metadata__l4_lookup_word_13
	bit<16> local_metadata__l4_lookup_word_24
	bit<8> local_metadata__first_frag5
	bit<8> local_metadata__ipv4_checksum_err6
	bit<16> Ingress_nexthop_id_0
	bit<8> Ingress_ttl_dec_0
	bit<32> Ingress_hash_0
	bit<32> Ingress_nexthop_1_group_id
	bit<32> Ingress_nexthop_1_member_id
	bit<16> IngressParser_parser_tmp
	bit<8> IngressParser_parser_tmp_1
}
metadata instanceof my_ingress_metadata_t

struct psa_ingress_output_metadata_t {
	bit<8> class_of_service
	bit<8> clone
	bit<16> clone_session_id
	bit<8> drop
	bit<8> resubmit
	bit<32> multicast_group
	bit<32> egress_port
}

struct psa_egress_output_metadata_t {
	bit<8> clone
	bit<16> clone_session_id
	bit<8> drop
}

struct psa_egress_deparser_input_metadata_t {
	bit<32> egress_port
}

action NoAction args none {
	return
}

action send args instanceof send_arg_t {
	mov m.psa_ingress_output_metadata_egress_port t.port
	mov m.Ingress_ttl_dec_0 0x0
	return
}

action drop args none {
	mov m.psa_ingress_output_metadata_drop 1
	return
}

action l3_switch args instanceof l3_switch_arg_t {
	mov h.ethernet.dst_addr t.new_mac_da
	mov h.ethernet.src_addr t.new_mac_sa
	mov m.Ingress_ttl_dec_0 0x1
	mov m.psa_ingress_output_metadata_egress_port t.port
	return
}

action set_nexthop args instanceof set_nexthop_arg_t {
	mov m.Ingress_nexthop_id_0 t.nexthop
	return
}

action nexthop_1_set_group_id args instanceof nexthop_1_set_group_id_arg_t {
	mov m.Ingress_nexthop_1_group_id t.group_id
	return
}

table ipv4_host_1 {
	key {
		h.ipv4.dst_addr exact
	}
	actions {
		set_nexthop
		NoAction
	}
	default_action NoAction args none
	size 0x400
}


table ipv4_host_2 {
	key {
		h.ipv4.src_addr exact
		h.ipv4.dst_addr exact
	}
	actions {
		set_nexthop
		NoAction
	}
	default_action NoAction args none
	size 0x10000
}


table ipv4_host_3 {
	key {
		m.local_metadata__l4_lookup_ipv4_src_addr0 exact
		m.local_metadata__l4_lookup_ipv4_dst_addr1 exact
		m.local_metadata__l4_lookup_ipv4_protocol2 exact
		m.local_metadata__l4_lookup_word_13 exact
		m.local_metadata__l4_lookup_word_24 exact
	}
	actions {
		set_nexthop
		NoAction
	}
	default_action NoAction args none
	size 0x10000
}


table ipv6_host {
	key {
		h.ipv6.dst_addr_hi exact
		h.ipv6.dst_addr_lo exact
	}
	actions {
		set_nexthop
		NoAction
	}
	default_action NoAction args none
	size 0x8000
}


table nexthop {
	key {
		m.Ingress_nexthop_id_0 exact
	}
	actions {
		nexthop_1_set_group_id
		NoAction
	}
	default_action NoAction args none
	size 0x4000
}


table nexthop_1_member_table {
	key {
		m.Ingress_nexthop_1_member_id exact
	}
	actions {
		send
		drop
		l3_switch
		NoAction
	}
	default_action NoAction args none
	size 0x4000
}


selector nexthop_1_group_table {
	group_id m.Ingress_nexthop_1_group_id
	selector {
		m.Ingress_hash_0
	}
	member_id m.Ingress_nexthop_1_member_id
	n_groups_max 1024
	n_members_per_group_max 65536
}

apply {
	rx m.psa_ingress_input_metadata_ingress_port
	mov m.psa_ingress_output_metadata_drop 0x0
	extract h.ethernet
	jmpeq MYIP_PARSE_VLAN_TAG h.ethernet.ether_type 0x8100
	jmpeq MYIP_PARSE_IPV4 h.ethernet.ether_type 0x800
	jmpeq MYIP_PARSE_IPV6 h.ethernet.ether_type 0x86dd
	jmp MYIP_ACCEPT
	MYIP_PARSE_VLAN_TAG :	extract h.vlan_tag_0
	jmpeq MYIP_PARSE_VLAN_TAG1 h.vlan_tag_0.ether_type 0x8100
	jmpeq MYIP_PARSE_IPV4 h.vlan_tag_0.ether_type 0x800
	jmp MYIP_ACCEPT
	MYIP_PARSE_VLAN_TAG1 :	extract h.vlan_tag_1
	jmpeq MYIP_PARSE_VLAN_TAG2 h.vlan_tag_1.ether_type 0x8100
	jmpeq MYIP_PARSE_IPV4 h.vlan_tag_1.ether_type 0x800
	jmp MYIP_ACCEPT
	MYIP_PARSE_VLAN_TAG2 :	mov m.psa_ingress_input_metadata_parser_error 0x3
	jmp MYIP_ACCEPT
	MYIP_PARSE_IPV4 :	extract h.ipv4
	mov h.cksum_state.state_0 0x0
	ckadd h.cksum_state.state_0 h.ipv4
	cksub h.cksum_state.state_0 h.ipv4.hdr_checksum
	mov m.local_metadata__l4_lookup_ipv4_dst_addr1 h.ipv4.dst_addr
	mov m.local_metadata__l4_lookup_ipv4_src_addr0 h.ipv4.src_addr
	mov m.local_metadata__l4_lookup_ipv4_protocol2 h.ipv4.protocol
	jmpeq MYIP_PARSE_IPV4_NO_OPTIONS h.ipv4.version_ihl 0x45
	jmp MYIP_ACCEPT
	MYIP_PARSE_IPV4_NO_OPTIONS :	mov m.IngressParser_parser_tmp h.cksum_state.state_0
	jmpeq LABEL_1TRUE m.IngressParser_parser_tmp h.ipv4.hdr_checksum
	mov m.IngressParser_parser_tmp_1 0x0
	jmp LABEL_1END
	LABEL_1TRUE :	mov m.IngressParser_parser_tmp_1 0x1
	LABEL_1END :	jmpneq LABEL_2END m.IngressParser_parser_tmp_1 0
	mov m.psa_ingress_input_metadata_parser_error 0x7
	jmp MYIP_ACCEPT
	LABEL_2END :	jmpneq MYIP_PARSE_IPV4_NO_OPTIONS_0 h.ipv4.flags_frag_offset 0x0
	jmpneq MYIP_PARSE_IPV4_NO_OPTIONS_0 h.ipv4.protocol 0x1
	jmp MYIP_PARSE_ICMP
	MYIP_PARSE_IPV4_NO_OPTIONS_0 :	jmpneq MYIP_PARSE_IPV4_NO_OPTIONS_1 h.ipv4.flags_frag_offset 0x0
	jmpneq MYIP_PARSE_IPV4_NO_OPTIONS_1 h.ipv4.protocol 0x2
	jmp MYIP_PARSE_IGMP
	MYIP_PARSE_IPV4_NO_OPTIONS_1 :	jmpneq MYIP_PARSE_IPV4_NO_OPTIONS_2 h.ipv4.flags_frag_offset 0x0
	jmpneq MYIP_PARSE_IPV4_NO_OPTIONS_2 h.ipv4.protocol 0x6
	jmp MYIP_PARSE_TCP
	MYIP_PARSE_IPV4_NO_OPTIONS_2 :	jmpneq MYIP_PARSE_IPV4_NO_OPTIONS_3 h.ipv4.flags_frag_offset 0x0
	jmpneq MYIP_PARSE_IPV4_NO_OPTIONS_3 h.ipv4.protocol 0x11
	jmp MYIP_PARSE_UDP
	MYIP_PARSE_IPV4_NO_OPTIONS_3 :	jmpneq MYIP_ACCEPT h.ipv4.flags_frag_offset 0x0
	jmp MYIP_PARSE_FIRST_FRAGMENT
	jmp MYIP_ACCEPT
	MYIP_PARSE_IPV6 :	extract h.ipv6
	jmpeq MYIP_PARSE_ICMP h.ipv6.next_hdr 0x1
	jmpeq MYIP_PARSE_IGMP h.ipv6.next_hdr 0x2
	jmpeq MYIP_PARSE_TCP h.ipv6.next_hdr 0x6
	jmpeq MYIP_PARSE_UDP h.ipv6.next_hdr 0x11
	jmp MYIP_PARSE_FIRST_FRAGMENT
	MYIP_PARSE_UDP :	extract h.udp
	mov m.local_metadata__l4_lookup_word_13 h.udp.src_port
	mov m.local_metadata__l4_lookup_word_24 h.udp.dst_port
	jmp MYIP_PARSE_FIRST_FRAGMENT
	MYIP_PARSE_TCP :	extract h.tcp
	mov m.local_metadata__l4_lookup_word_13 h.tcp.src_port
	mov m.local_metadata__l4_lookup_word_24 h.tcp.dst_port
	jmp MYIP_PARSE_FIRST_FRAGMENT
	MYIP_PARSE_IGMP :	extract h.igmp
	mov m.local_metadata__l4_lookup_word_13 h.igmp.type_code
	mov m.local_metadata__l4_lookup_word_24 h.igmp.checksum
	jmp MYIP_PARSE_FIRST_FRAGMENT
	MYIP_PARSE_ICMP :	extract h.icmp
	mov m.local_metadata__l4_lookup_word_13 h.icmp.type_code
	mov m.local_metadata__l4_lookup_word_24 h.icmp.checksum
	MYIP_PARSE_FIRST_FRAGMENT :	mov m.local_metadata__first_frag5 0x1
	MYIP_ACCEPT :	mov m.Ingress_nexthop_id_0 0x0
	mov m.Ingress_ttl_dec_0 0x0
	mov m.Ingress_hash_0 0x0
	jmpnv LABEL_3END h.ipv4
	jmpnv LABEL_3END h.ipv6
	mov m.local_metadata__first_frag5 0x0
	LABEL_3END :	jmpnv LABEL_4FALSE h.ipv4
	jmplt LABEL_4END h.ipv4.ttl 0x2
	table ipv4_host_1
	jmpnh LABEL_6FALSE
	jmp LABEL_4END
	LABEL_6FALSE :	table ipv4_host_2
	jmpnh LABEL_7FALSE
	jmp LABEL_4END
	LABEL_7FALSE :	table ipv4_host_3
	jmp LABEL_4END
	LABEL_4FALSE :	jmpnv LABEL_4END h.ipv6
	jmplt LABEL_4END h.ipv6.hop_limit 0x2
	table ipv6_host
	LABEL_4END :	mov m.Ingress_nexthop_1_member_id 0x0
	mov m.Ingress_nexthop_1_group_id 0x0
	table nexthop
	table nexthop_1_group_table
	table nexthop_1_member_table
	jmpnv LABEL_10FALSE h.ipv4
	cksub h.cksum_state.state_0 h.ipv4.ttl
	sub h.ipv4.ttl m.Ingress_ttl_dec_0
	ckadd h.cksum_state.state_0 h.ipv4.ttl
	mov h.ipv4.hdr_checksum h.cksum_state.state_0
	jmp LABEL_10END
	LABEL_10FALSE :	jmpnv LABEL_10END h.ipv6
	sub h.ipv6.hop_limit m.Ingress_ttl_dec_0
	LABEL_10END :	jmpneq LABEL_DROP m.psa_ingress_output_metadata_drop 0x0
	emit h.ethernet
	emit h.vlan_tag_0
	emit h.vlan_tag_1
	emit h.ipv4
	emit h.ipv6
	emit h.icmp
	emit h.igmp
	emit h.tcp
	emit h.udp
	tx m.psa_ingress_output_metadata_egress_port
	LABEL_DROP :	drop
}