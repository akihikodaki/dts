
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

header ethernet instanceof ethernet_h
header ipv4 instanceof ipv4_h
header icmp instanceof icmp_h
header igmp instanceof igmp_h
header tcp instanceof tcp_h
header udp instanceof udp_h

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
	bit<16> Ingress_csum_inc_0
}
metadata instanceof my_ingress_metadata_t

struct l3_switch_arg_t {
	bit<32> port
	bit<48> new_mac_da
	bit<48> new_mac_sa
}

struct send_arg_t {
	bit<32> port
}

struct set_nexthop_arg_t {
	bit<16> nexthop
}

action NoAction args none {
	return
}

action send args instanceof send_arg_t {
	mov m.psa_ingress_output_metadata_egress_port t.port
	mov m.Ingress_ttl_dec_0 0x0
	mov m.Ingress_csum_inc_0 0x0
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
	mov m.Ingress_csum_inc_0 0x1
	mov m.psa_ingress_output_metadata_egress_port t.port
	return
}

action set_nexthop args instanceof set_nexthop_arg_t {
	mov m.Ingress_nexthop_id_0 t.nexthop
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

table nexthop {
	key {
		m.Ingress_nexthop_id_0 exact
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

apply {
	rx m.psa_ingress_input_metadata_ingress_port
	mov m.psa_ingress_output_metadata_drop 0x0
	extract h.ethernet
	jmpeq MYIP_PARSE_IPV4 h.ethernet.ether_type 0x800
	jmp MYIP_ACCEPT
	MYIP_PARSE_IPV4 :	extract h.ipv4
	mov m.local_metadata__l4_lookup_ipv4_dst_addr1 h.ipv4.dst_addr
	mov m.local_metadata__l4_lookup_ipv4_src_addr0 h.ipv4.src_addr
	mov m.local_metadata__l4_lookup_ipv4_protocol2 h.ipv4.protocol
	jmpeq MYIP_PARSE_ICMP h.ipv4.protocol 0x1
	jmpeq MYIP_PARSE_IGMP h.ipv4.protocol 0x2
	jmpeq MYIP_PARSE_TCP h.ipv4.protocol 0x6
	jmpeq MYIP_PARSE_UDP h.ipv4.protocol 0x11
	jmp MYIP_ACCEPT
	MYIP_PARSE_UDP :	extract h.udp
	mov m.local_metadata__l4_lookup_word_13 h.udp.src_port
	mov m.local_metadata__l4_lookup_word_24 h.udp.dst_port
	jmp MYIP_ACCEPT
	MYIP_PARSE_TCP :	extract h.tcp
	mov m.local_metadata__l4_lookup_word_13 h.tcp.src_port
	mov m.local_metadata__l4_lookup_word_24 h.tcp.dst_port
	jmp MYIP_ACCEPT
	MYIP_PARSE_ICMP :	extract h.icmp
	mov m.local_metadata__l4_lookup_word_13 h.icmp.type_code
	mov m.local_metadata__l4_lookup_word_24 h.icmp.checksum
	jmp MYIP_ACCEPT
	MYIP_PARSE_IGMP :	extract h.igmp
	mov m.local_metadata__first_frag5 0x1
	mov m.local_metadata__l4_lookup_word_13 h.igmp.type_code
	mov m.local_metadata__l4_lookup_word_24 h.igmp.checksum
	MYIP_ACCEPT :	mov m.Ingress_nexthop_id_0 0x0
	mov m.Ingress_ttl_dec_0 0x0
	mov m.Ingress_csum_inc_0 0x0
	table ipv4_host_1
	jmph LABEL_0END
	table ipv4_host_2
	jmph LABEL_0END
	table ipv4_host_3
	LABEL_0END :	table nexthop
	sub h.ipv4.ttl m.Ingress_ttl_dec_0
	add h.ipv4.hdr_checksum m.Ingress_csum_inc_0
	jmpneq LABEL_DROP m.psa_ingress_output_metadata_drop 0x0
	emit h.ethernet
	emit h.ipv4
	emit h.icmp
	emit h.igmp
	emit h.tcp
	emit h.udp
	tx m.psa_ingress_output_metadata_egress_port
	LABEL_DROP : drop
}
