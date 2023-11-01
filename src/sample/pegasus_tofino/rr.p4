#include <tofino/intrinsic_metadata.p4>
#include "tofino/stateful_alu_blackbox.p4"
#include <tofino/constants.p4>

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

#define ETHERTYPE_IPV4  0x800
#define PROTO_UDP       0x11
#define PEGASUS_ID      0x5047

#define OP_GET          0x0
#define OP_PUT          0x1
#define OP_DEL          0x2
#define OP_REP_R        0x3
#define OP_REP_W        0x4
#define OP_MGR_REQ      0x5
#define OP_MGR_ACK      0x6
#define OP_DEC          0xF

#define RNODE_NONE      0x7F
#define RKEY_NONE       0x7F
#define MAX_RKEY_RATE   0x7FFF

#define NNODES          32
#define MAX_REPLICAS    16

header_type ethernet_t {
    fields {
        dstAddr : 48;
        srcAddr : 48;
        etherType : 16;
    }
}

header ethernet_t ethernet;

header_type ipv4_t {
    fields {
        version : 4;
        ihl : 4;
        diffserv : 8;
        totalLen : 16;
        identification : 16;
        flags : 3;
        fragOffset : 13;
        ttl : 8;
        protocol : 8;
        hdrChecksum : 16;
        srcAddr : 32;
        dstAddr : 32;
    }
}

header ipv4_t ipv4;

header_type udp_t {
    fields {
        srcPort : 16;
        dstPort : 16;
        len : 16;
        checksum : 16;
    }
}

header udp_t udp;

header_type apphdr_t {
    fields {
        id : 16;
    }
}

header apphdr_t apphdr;

header_type pegasus_t {
    fields {
        op : 8;
        keyhash : 32;
        node : 8;
        load : 16;
        ver : 32;
        debug_node : 8;
        debug_load : 16;
    }
}

header pegasus_t pegasus;

header_type metadata_t {
    fields {
        rkey_index : 32;
        rset_num_ack : 8;
        rset_size : 8;
        rset_index: 8;
        node : 8;
        load : 16;
        ver_matched : 1;
    }
}

metadata metadata_t meta;

/*************************************************************************
*********************** STATEFUL MEMORY  *********************************
*************************************************************************/
/*
   next version number
*/
register reg_ver_next {
    width: 32;
    instance_count: 1;
}
/*
   version number of latest completed write
 */
register reg_rkey_ver_completed {
    width: 32;
    instance_count: 32;
}
/*
   rkey access rate counter
 */
register reg_rkey_rate_counter {
    width: 16;
    instance_count: 32;
}
/*
   round-robin counter
*/
register reg_rr_rkey_counter {
    // per key counter
    width: 8;
    instance_count: 32;
}
register reg_rr_global_counter {
    width: 8;
    instance_count: 1;
}
register reg_rset_num_ack {
    width: 8;
    instance_count: 32;
}
register reg_rset_size {
    width: 8;
    instance_count: 32;
}
register reg_rset_1 {
    width: 8;
    instance_count: 32;
}
register reg_rset_2 {
    width: 8;
    instance_count: 32;
}
register reg_rset_3 {
    width: 8;
    instance_count: 32;
}
register reg_rset_4 {
    width: 8;
    instance_count: 32;
}
register reg_rset_5 {
    width: 8;
    instance_count: 32;
}
register reg_rset_6 {
    width: 8;
    instance_count: 32;
}
register reg_rset_7 {
    width: 8;
    instance_count: 32;
}
register reg_rset_8 {
    width: 8;
    instance_count: 32;
}
register reg_rset_9 {
    width: 8;
    instance_count: 32;
}
register reg_rset_10 {
    width: 8;
    instance_count: 32;
}
register reg_rset_11 {
    width: 8;
    instance_count: 32;
}
register reg_rset_12 {
    width: 8;
    instance_count: 32;
}
register reg_rset_13 {
    width: 8;
    instance_count: 32;
}
register reg_rset_14 {
    width: 8;
    instance_count: 32;
}
register reg_rset_15 {
    width: 8;
    instance_count: 32;
}
register reg_rset_16 {
    width: 8;
    instance_count: 32;
}
/*
   Read/Write ratio counter
 */
register reg_rkey_read_counter {
    width: 16;
    instance_count: 32;
}
register reg_rkey_write_counter {
    width: 16;
    instance_count: 32;
}
/*************************************************************************
*********************** CHECKSUM *****************************************
*************************************************************************/

field_list ipv4_field_list {
    ipv4.version;
    ipv4.ihl;
    ipv4.diffserv;
    ipv4.totalLen;
    ipv4.identification;
    ipv4.flags;
    ipv4.fragOffset;
    ipv4.ttl;
    ipv4.protocol;
    ipv4.srcAddr;
    ipv4.dstAddr;
}

field_list_calculation ipv4_chksum_calc {
    input {
        ipv4_field_list;
    }
    algorithm : csum16;
    output_width: 16;
}

calculated_field ipv4.hdrChecksum {
    update ipv4_chksum_calc;
}

/*************************************************************************
*********************** P A R S E R S  ***********************************
*************************************************************************/

parser start {
    return parse_ethernet;
}

parser parse_ethernet {
    extract(ethernet);
    return select(latest.etherType) {
        ETHERTYPE_IPV4: parse_ipv4;
        default: ingress;
    }
}

parser parse_ipv4 {
    extract(ipv4);
    return select(latest.protocol) {
        PROTO_UDP: parse_udp;
        default: ingress;
    }
}

parser parse_udp {
    extract(udp);
    return parse_apphdr;
}

parser parse_apphdr {
    extract(apphdr);
    return select(latest.id) {
        PEGASUS_ID: parse_pegasus;
        default: ingress;
    }
}

parser parse_pegasus {
    extract(pegasus);
    return ingress;
}

/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

/*
   L2 forward
*/
action nop() {
}

action _drop() {
    drop();
}

action l2_forward(port) {
    modify_field(ig_intr_md_for_tm.ucast_egress_port, port);
}

table tab_l2_forward {
    reads {
        ethernet.dstAddr: exact;
    }
    actions {
        l2_forward;
        _drop;
    }
    size: 1024;
}

/*
   node forward
*/
action node_forward(mac_addr, ip_addr, udp_addr, port) {
    modify_field(ethernet.dstAddr, mac_addr);
    modify_field(ipv4.dstAddr, ip_addr);
    modify_field(udp.dstPort, udp_addr);
    modify_field(ig_intr_md_for_tm.ucast_egress_port, port);
}

table tab_node_forward {
    reads {
        meta.node: exact;
    }
    actions {
        node_forward;
        _drop;
    }
    size: 1024;
}

/*
   drop
 */
action do_drop() {
    _drop();
}

table tab_do_drop {
    actions {
        do_drop;
    }
    default_action: do_drop;
    size: 1;
}

/*
   replicated keys
*/
action lookup_rkey(rkey_index) {
    modify_field(meta.rkey_index, rkey_index);
}

action set_default_dst_node() {
    bit_and(meta.node, pegasus.keyhash, 3);
    modify_field(meta.rkey_index, RKEY_NONE);
}

@pragma stage 0
table tab_replicated_keys {
    reads {
        pegasus.keyhash: exact;
    }
    actions {
        lookup_rkey;
        set_default_dst_node;
    }
    default_action: set_default_dst_node;
    size: 32;
}

/*
   inc rkey rate counter
 */
blackbox stateful_alu sa_inc_rkey_rate_counter {
    reg: reg_rkey_rate_counter;
    condition_lo: register_lo < MAX_RKEY_RATE;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: register_lo + 1;
}
action inc_rkey_rate_counter() {
    sa_inc_rkey_rate_counter.execute_stateful_alu(meta.rkey_index);
}
@pragma stage 1
table tab_inc_rkey_rate_counter {
    actions {
        inc_rkey_rate_counter;
    }
    default_action: inc_rkey_rate_counter;
    size: 1;
}

/*
   access round-robin counter
 */
blackbox stateful_alu sa_access_rr_rkey_counter {
    reg: reg_rr_rkey_counter;
    condition_lo: register_lo >= meta.rset_size - 1;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: 0;
    update_lo_2_predicate: not condition_lo;
    update_lo_2_value: register_lo + 1;
    output_value: alu_lo;
    output_dst: meta.rset_index;
}
blackbox stateful_alu sa_access_rr_global_counter {
    reg: reg_rr_global_counter;
    condition_lo: register_lo >= NNODES - 1;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: 0;
    update_lo_2_predicate: not condition_lo;
    update_lo_2_value: register_lo + 1;
    output_value: alu_lo;
    output_dst: meta.node;
}

action access_rr_rkey_counter() {
    sa_access_rr_rkey_counter.execute_stateful_alu(meta.rkey_index);
}
action access_rr_global_counter() {
    sa_access_rr_global_counter.execute_stateful_alu(0);
}

@pragma stage 3
table tab_access_rr_rkey_counter {
    actions {
        access_rr_rkey_counter;
    }
    default_action: access_rr_rkey_counter;
    size: 1;
}
@pragma stage 3
table tab_access_rr_global_counter {
    actions {
        access_rr_global_counter;
    }
    default_action: access_rr_global_counter;
    size: 1;
}

/*
   get/set/inc rset_num_ack
 */
blackbox stateful_alu sa_get_rset_num_ack {
    reg: reg_rset_num_ack;
    output_value: register_lo;
    output_dst: meta.rset_num_ack;
}
blackbox stateful_alu sa_set_rset_num_ack {
    reg: reg_rset_num_ack;
    update_lo_1_value: 1;
}
blackbox stateful_alu sa_inc_rset_num_ack {
    reg: reg_rset_num_ack;
    condition_lo: register_lo < NNODES;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: register_lo + 1;
}

action get_rset_num_ack() {
    sa_get_rset_num_ack.execute_stateful_alu(meta.rkey_index);
}
action set_rset_num_ack() {
    sa_set_rset_num_ack.execute_stateful_alu(meta.rkey_index);
}
action inc_rset_num_ack() {
    sa_inc_rset_num_ack.execute_stateful_alu(meta.rkey_index);
}

@pragma stage 2
table tab_get_rset_num_ack {
    actions {
        get_rset_num_ack;
    }
    default_action: get_rset_num_ack;
    size: 1;
}
@pragma stage 2
table tab_set_rset_num_ack {
    actions {
        set_rset_num_ack;
    }
    default_action: set_rset_num_ack;
    size: 1;
}
@pragma stage 2
table tab_inc_rset_num_ack {
    actions {
        inc_rset_num_ack;
    }
    default_action: inc_rset_num_ack;
    size: 1;
}

/*
   get/set/inc rset_size
 */
blackbox stateful_alu sa_get_rset_size {
    reg: reg_rset_size;
    output_value: register_lo;
    output_dst: meta.rset_size;
}
blackbox stateful_alu sa_set_rset_size {
    reg: reg_rset_size;
    update_lo_1_value: 1;
}
blackbox stateful_alu sa_inc_rset_size {
    reg: reg_rset_size;
    condition_lo: register_lo < MAX_REPLICAS;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: register_lo + 1;
    output_value: register_lo;
    output_dst: meta.rset_size;
}

action get_rset_size() {
    sa_get_rset_size.execute_stateful_alu(meta.rkey_index);
}
action set_rset_size() {
    sa_set_rset_size.execute_stateful_alu(meta.rkey_index);
}
action inc_rset_size() {
    sa_inc_rset_size.execute_stateful_alu(meta.rkey_index);
}

@pragma stage 2
table tab_get_rset_size {
    actions {
        get_rset_size;
    }
    default_action: get_rset_size;
    size: 1;
}
@pragma stage 2
table tab_set_rset_size {
    actions {
        set_rset_size;
    }
    default_action: set_rset_size;
    size: 1;
}
@pragma stage 2
table tab_inc_rset_size {
    actions {
        inc_rset_size;
    }
    default_action: inc_rset_size;
    size: 1;
}

/*
   get/set/install rset
 */
blackbox stateful_alu sa_get_rset_1 {
    reg: reg_rset_1;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_2 {
    reg: reg_rset_2;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_3 {
    reg: reg_rset_3;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_4 {
    reg: reg_rset_4;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_5 {
    reg: reg_rset_5;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_6 {
    reg: reg_rset_6;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_7 {
    reg: reg_rset_7;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_8 {
    reg: reg_rset_8;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_9 {
    reg: reg_rset_9;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_10 {
    reg: reg_rset_10;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_11 {
    reg: reg_rset_11;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_12 {
    reg: reg_rset_12;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_13 {
    reg: reg_rset_13;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_14 {
    reg: reg_rset_14;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_15 {
    reg: reg_rset_15;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_get_rset_16 {
    reg: reg_rset_16;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_set_rset_1 {
    reg: reg_rset_1;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_2 {
    reg: reg_rset_2;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_3 {
    reg: reg_rset_3;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_4 {
    reg: reg_rset_4;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_5 {
    reg: reg_rset_5;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_6 {
    reg: reg_rset_6;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_7 {
    reg: reg_rset_7;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_8 {
    reg: reg_rset_8;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_9 {
    reg: reg_rset_9;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_10 {
    reg: reg_rset_10;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_11 {
    reg: reg_rset_11;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_12 {
    reg: reg_rset_12;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_13 {
    reg: reg_rset_13;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_14 {
    reg: reg_rset_14;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_15 {
    reg: reg_rset_15;
    update_lo_1_value: meta.node;
}
blackbox stateful_alu sa_install_rset_16 {
    reg: reg_rset_16;
    update_lo_1_value: meta.node;
}

action get_rset_1() {
    sa_get_rset_1.execute_stateful_alu(meta.rkey_index);
}
action get_rset_2() {
    sa_get_rset_2.execute_stateful_alu(meta.rkey_index);
}
action get_rset_3() {
    sa_get_rset_3.execute_stateful_alu(meta.rkey_index);
}
action get_rset_4() {
    sa_get_rset_4.execute_stateful_alu(meta.rkey_index);
}
action get_rset_5() {
    sa_get_rset_5.execute_stateful_alu(meta.rkey_index);
}
action get_rset_6() {
    sa_get_rset_6.execute_stateful_alu(meta.rkey_index);
}
action get_rset_7() {
    sa_get_rset_7.execute_stateful_alu(meta.rkey_index);
}
action get_rset_8() {
    sa_get_rset_8.execute_stateful_alu(meta.rkey_index);
}
action get_rset_9() {
    sa_get_rset_9.execute_stateful_alu(meta.rkey_index);
}
action get_rset_10() {
    sa_get_rset_10.execute_stateful_alu(meta.rkey_index);
}
action get_rset_11() {
    sa_get_rset_11.execute_stateful_alu(meta.rkey_index);
}
action get_rset_12() {
    sa_get_rset_12.execute_stateful_alu(meta.rkey_index);
}
action get_rset_13() {
    sa_get_rset_13.execute_stateful_alu(meta.rkey_index);
}
action get_rset_14() {
    sa_get_rset_14.execute_stateful_alu(meta.rkey_index);
}
action get_rset_15() {
    sa_get_rset_15.execute_stateful_alu(meta.rkey_index);
}
action get_rset_16() {
    sa_get_rset_16.execute_stateful_alu(meta.rkey_index);
}
action set_rset_1() {
    sa_set_rset_1.execute_stateful_alu(meta.rkey_index);
}
action install_rset_2() {
    sa_install_rset_2.execute_stateful_alu(meta.rkey_index);
}
action install_rset_3() {
    sa_install_rset_3.execute_stateful_alu(meta.rkey_index);
}
action install_rset_4() {
    sa_install_rset_4.execute_stateful_alu(meta.rkey_index);
}
action install_rset_5() {
    sa_install_rset_5.execute_stateful_alu(meta.rkey_index);
}
action install_rset_6() {
    sa_install_rset_6.execute_stateful_alu(meta.rkey_index);
}
action install_rset_7() {
    sa_install_rset_7.execute_stateful_alu(meta.rkey_index);
}
action install_rset_8() {
    sa_install_rset_8.execute_stateful_alu(meta.rkey_index);
}
action install_rset_9() {
    sa_install_rset_9.execute_stateful_alu(meta.rkey_index);
}
action install_rset_10() {
    sa_install_rset_10.execute_stateful_alu(meta.rkey_index);
}
action install_rset_11() {
    sa_install_rset_11.execute_stateful_alu(meta.rkey_index);
}
action install_rset_12() {
    sa_install_rset_12.execute_stateful_alu(meta.rkey_index);
}
action install_rset_13() {
    sa_install_rset_13.execute_stateful_alu(meta.rkey_index);
}
action install_rset_14() {
    sa_install_rset_14.execute_stateful_alu(meta.rkey_index);
}
action install_rset_15() {
    sa_install_rset_15.execute_stateful_alu(meta.rkey_index);
}
action install_rset_16() {
    sa_install_rset_16.execute_stateful_alu(meta.rkey_index);
}


@pragma stage 4
table tab_get_rset_1 {
    actions {
        get_rset_1;
    }
    default_action: get_rset_1;
    size: 1;
}
@pragma stage 4
table tab_get_rset_2 {
    actions {
        get_rset_2;
    }
    default_action: get_rset_2;
    size: 1;
}
@pragma stage 4
table tab_get_rset_3 {
    actions {
        get_rset_3;
    }
    default_action: get_rset_3;
    size: 1;
}
@pragma stage 4
table tab_get_rset_4 {
    actions {
        get_rset_4;
    }
    default_action: get_rset_4;
    size: 1;
}
@pragma stage 5
table tab_get_rset_5 {
    actions {
        get_rset_5;
    }
    default_action: get_rset_5;
    size: 1;
}
@pragma stage 5
table tab_get_rset_6 {
    actions {
        get_rset_6;
    }
    default_action: get_rset_6;
    size: 1;
}
@pragma stage 5
table tab_get_rset_7 {
    actions {
        get_rset_7;
    }
    default_action: get_rset_7;
    size: 1;
}
@pragma stage 5
table tab_get_rset_8 {
    actions {
        get_rset_8;
    }
    default_action: get_rset_8;
    size: 1;
}
@pragma stage 6
table tab_get_rset_9 {
    actions {
        get_rset_9;
    }
    default_action: get_rset_9;
    size: 1;
}
@pragma stage 6
table tab_get_rset_10 {
    actions {
        get_rset_10;
    }
    default_action: get_rset_10;
    size: 1;
}
@pragma stage 6
table tab_get_rset_11 {
    actions {
        get_rset_11;
    }
    default_action: get_rset_11;
    size: 1;
}
@pragma stage 6
table tab_get_rset_12 {
    actions {
        get_rset_12;
    }
    default_action: get_rset_12;
    size: 1;
}
@pragma stage 7
table tab_get_rset_13 {
    actions {
        get_rset_13;
    }
    default_action: get_rset_13;
    size: 1;
}
@pragma stage 7
table tab_get_rset_14 {
    actions {
        get_rset_14;
    }
    default_action: get_rset_14;
    size: 1;
}
@pragma stage 7
table tab_get_rset_15 {
    actions {
        get_rset_15;
    }
    default_action: get_rset_15;
    size: 1;
}
@pragma stage 7
table tab_get_rset_16 {
    actions {
        get_rset_16;
    }
    default_action: get_rset_16;
    size: 1;
}
@pragma stage 4
table tab_set_rset_1 {
    actions {
        set_rset_1;
    }
    default_action: set_rset_1;
    size: 1;
}
@pragma stage 4
table tab_install_rset_2 {
    actions {
        install_rset_2;
    }
    default_action: install_rset_2;
    size: 1;
}
@pragma stage 4
table tab_install_rset_3 {
    actions {
        install_rset_3;
    }
    default_action: install_rset_3;
    size: 1;
}
@pragma stage 4
table tab_install_rset_4 {
    actions {
        install_rset_4;
    }
    default_action: install_rset_4;
    size: 1;
}
@pragma stage 5
table tab_install_rset_5 {
    actions {
        install_rset_5;
    }
    default_action: install_rset_5;
    size: 1;
}
@pragma stage 5
table tab_install_rset_6 {
    actions {
        install_rset_6;
    }
    default_action: install_rset_6;
    size: 1;
}
@pragma stage 5
table tab_install_rset_7 {
    actions {
        install_rset_7;
    }
    default_action: install_rset_7;
    size: 1;
}
@pragma stage 5
table tab_install_rset_8 {
    actions {
        install_rset_8;
    }
    default_action: install_rset_8;
    size: 1;
}
@pragma stage 6
table tab_install_rset_9 {
    actions {
        install_rset_9;
    }
    default_action: install_rset_9;
    size: 1;
}
@pragma stage 6
table tab_install_rset_10 {
    actions {
        install_rset_10;
    }
    default_action: install_rset_10;
    size: 1;
}
@pragma stage 6
table tab_install_rset_11 {
    actions {
        install_rset_11;
    }
    default_action: install_rset_11;
    size: 1;
}
@pragma stage 6
table tab_install_rset_12 {
    actions {
        install_rset_12;
    }
    default_action: install_rset_12;
    size: 1;
}
@pragma stage 7
table tab_install_rset_13 {
    actions {
        install_rset_13;
    }
    default_action: install_rset_13;
    size: 1;
}
@pragma stage 7
table tab_install_rset_14 {
    actions {
        install_rset_14;
    }
    default_action: install_rset_14;
    size: 1;
}
@pragma stage 7
table tab_install_rset_15 {
    actions {
        install_rset_15;
    }
    default_action: install_rset_15;
    size: 1;
}
@pragma stage 7
table tab_install_rset_16 {
    actions {
        install_rset_16;
    }
    default_action: install_rset_16;
    size: 1;
}

/*
   version number
 */
blackbox stateful_alu sa_get_ver_next {
    reg: reg_ver_next;
    update_lo_1_value: register_lo + 1;
    output_value: alu_lo;
    output_dst: pegasus.ver;
}
blackbox stateful_alu sa_compare_rkey_ver_completed {
    reg: reg_rkey_ver_completed;
    condition_lo: pegasus.ver == register_lo;
    output_predicate: condition_lo;
    output_value: combined_predicate;
    output_dst: meta.ver_matched;
}
blackbox stateful_alu sa_set_rkey_ver_completed {
    reg: reg_rkey_ver_completed;
    condition_lo: pegasus.ver > register_lo;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: pegasus.ver;
    output_predicate: condition_lo;
    output_value: combined_predicate;
    output_dst: meta.ver_matched;
}

action get_ver_next() {
    sa_get_ver_next.execute_stateful_alu(meta.rkey_index);
}
action compare_rkey_ver_completed() {
    sa_compare_rkey_ver_completed.execute_stateful_alu(meta.rkey_index);
}
action set_rkey_ver_completed() {
    sa_set_rkey_ver_completed.execute_stateful_alu(meta.rkey_index);
}

@pragma stage 1
table tab_get_ver_next {
    actions {
        get_ver_next;
    }
    default_action: get_ver_next;
    size: 1;
}
@pragma stage 1
table tab_compare_rkey_ver_completed {
    actions {
        compare_rkey_ver_completed;
    }
    default_action: compare_rkey_ver_completed;
    size: 1;
}
@pragma stage 1
table tab_set_rkey_ver_completed {
    actions {
        set_rkey_ver_completed;
    }
    default_action: set_rkey_ver_completed;
    size: 1;
}

/*
   rw counter
 */
blackbox stateful_alu sa_inc_rkey_read_counter {
    reg: reg_rkey_read_counter;
    update_lo_1_value: register_lo + 1;
}
blackbox stateful_alu sa_inc_rkey_write_counter {
    reg: reg_rkey_write_counter;
    update_lo_1_value: register_lo + 1;
}

action inc_rkey_read_counter() {
    sa_inc_rkey_read_counter.execute_stateful_alu(meta.rkey_index);
}
action inc_rkey_write_counter() {
    sa_inc_rkey_write_counter.execute_stateful_alu(meta.rkey_index);
}

table tab_inc_rkey_read_counter {
    actions {
        inc_rkey_read_counter;
    }
    default_action: inc_rkey_read_counter;
    size: 1;
}
table tab_inc_rkey_write_counter {
    actions {
        inc_rkey_write_counter;
    }
    default_action: inc_rkey_write_counter;
    size: 1;
}

/*
   copy header
 */
action copy_pegasus_header() {
    modify_field(meta.node, pegasus.node);
    modify_field(meta.load, pegasus.load);
}

table tab_copy_pegasus_header_a {
    actions {
        copy_pegasus_header;
    }
    default_action: copy_pegasus_header;
    size: 1;
}
table tab_copy_pegasus_header_b {
    actions {
        copy_pegasus_header;
    }
    default_action: copy_pegasus_header;
    size: 1;
}
table tab_copy_pegasus_header_c {
    actions {
        copy_pegasus_header;
    }
    default_action: copy_pegasus_header;
    size: 1;
}

control process_dec {
    apply(tab_do_drop);
}

control process_mgr_req {
    apply(tab_l2_forward);
}

control process_mgr_ack {
    if (meta.rkey_index != RKEY_NONE) {
        apply(tab_copy_pegasus_header_a);
        apply(tab_compare_rkey_ver_completed);
        if (meta.ver_matched != 0) {
            apply(tab_inc_rset_num_ack);
            apply(tab_inc_rset_size);
            if (meta.rset_size == 1) {
                apply(tab_install_rset_2);
            } else if (meta.rset_size == 2) {
                apply(tab_install_rset_3);
            } else if (meta.rset_size == 3) {
                apply(tab_install_rset_4);
            } else if (meta.rset_size == 4) {
                apply(tab_install_rset_5);
            } else if (meta.rset_size == 5) {
                apply(tab_install_rset_6);
            } else if (meta.rset_size == 6) {
                apply(tab_install_rset_7);
            } else if (meta.rset_size == 7) {
                apply(tab_install_rset_8);
            } else if (meta.rset_size == 8) {
                apply(tab_install_rset_9);
            } else if (meta.rset_size == 9) {
                apply(tab_install_rset_10);
            } else if (meta.rset_size == 10) {
                apply(tab_install_rset_11);
            } else if (meta.rset_size == 11) {
                apply(tab_install_rset_12);
            } else if (meta.rset_size == 12) {
                apply(tab_install_rset_13);
            } else if (meta.rset_size == 13) {
                apply(tab_install_rset_14);
            } else if (meta.rset_size == 14) {
                apply(tab_install_rset_15);
            } else if (meta.rset_size == 15) {
                apply(tab_install_rset_16);
            }
        }
    }
    apply(tab_do_drop);
}

control process_reply {
    if (meta.rkey_index != RKEY_NONE and pegasus.op == OP_REP_W) {
        apply(tab_copy_pegasus_header_b);
        apply(tab_set_rkey_ver_completed);
        if (meta.ver_matched != 0) {
            apply(tab_set_rset_num_ack);
            apply(tab_set_rset_size);
            apply(tab_set_rset_1);
        }
    }
    apply(tab_l2_forward);
}

control process_request {
    if (meta.rkey_index != RKEY_NONE) {
        apply(tab_inc_rkey_rate_counter);
        if (pegasus.op == OP_GET) {
            process_replicated_read();
        } else {
            process_replicated_write();
        }
    } else {
        apply(tab_copy_pegasus_header_c);
    }
    apply(tab_node_forward);
}

control process_replicated_read {
    apply(tab_inc_rkey_read_counter);
    apply(tab_get_rset_num_ack);
    apply(tab_get_rset_size);
    if (meta.rset_num_ack != NNODES) {
        apply(tab_access_rr_rkey_counter);
        if (meta.rset_index == 0) {
            apply(tab_get_rset_1);
        } else if (meta.rset_index == 1) {
            apply(tab_get_rset_2);
        } else if (meta.rset_index == 2) {
            apply(tab_get_rset_3);
        } else if (meta.rset_index == 3) {
            apply(tab_get_rset_4);
        } else if (meta.rset_index == 4) {
            apply(tab_get_rset_5);
        } else if (meta.rset_index == 5) {
            apply(tab_get_rset_6);
        } else if (meta.rset_index == 6) {
            apply(tab_get_rset_7);
        } else if (meta.rset_index == 7) {
            apply(tab_get_rset_8);
        } else if (meta.rset_index == 8) {
            apply(tab_get_rset_9);
        } else if (meta.rset_index == 9) {
            apply(tab_get_rset_10);
        } else if (meta.rset_index == 10) {
            apply(tab_get_rset_11);
        } else if (meta.rset_index == 11) {
            apply(tab_get_rset_12);
        } else if (meta.rset_index == 12) {
            apply(tab_get_rset_13);
        } else if (meta.rset_index == 13) {
            apply(tab_get_rset_14);
        } else if (meta.rset_index == 14) {
            apply(tab_get_rset_15);
        } else if (meta.rset_index == 15) {
            apply(tab_get_rset_16);
        }
    } else {
        apply(tab_access_rr_global_counter);
    }
}

control process_replicated_write {
    apply(tab_get_ver_next);
    apply(tab_inc_rkey_write_counter);
    apply(tab_access_rr_global_counter);
}

control ingress {
    if (valid(pegasus)) {
        if (pegasus.op == OP_DEC) {
            process_dec();
        } else if (pegasus.op == OP_MGR_REQ) {
            process_mgr_req();
        } else {
            apply(tab_replicated_keys);
            if (pegasus.op == OP_REP_R or pegasus.op == OP_REP_W) {
                process_reply();
            } else if (pegasus.op == OP_MGR_ACK) {
                process_mgr_ack();
            } else {
                process_request();
            }
        }
    } else {
        apply(tab_l2_forward);
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control egress {
}
