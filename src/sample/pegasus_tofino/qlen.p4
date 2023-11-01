#include <tofino/intrinsic_metadata.p4>
#include "tofino/stateful_alu_blackbox.p4"
#include <tofino/constants.p4>

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

#define ETHERTYPE_IPV4  0x800
#define PROTO_UDP       0x11
#define PEGASUS_ID      0x5047
#define HASH_MASK       0x3 // Max 4 nodes
#define MAX_REPLICAS    0x4
#define OP_GET          0x0
#define OP_PUT          0x1
#define OP_DEL          0x2
#define OP_REP          0x3
#define AVG_LOAD_SHIFT  0x2
#define RNODE_NONE      0x7F

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
    }
}

header pegasus_t pegasus;

header_type metadata_t {
    fields {
        // Node load stats
        total_node_load : 16;
        min_node : 8;
        min_node_load : 16;
        // Replica nodes
        rkey_index : 32;
        rnode_1 : 8;
        rnode_2 : 8;
        rnode_3 : 8;
        rnode_4 : 8;
        min_rload : 16;
        // Temporary variables
        tmp_node : 8;
        tmp_node_1 : 8;
        tmp_load : 16;
    }
}

metadata metadata_t meta;

/*************************************************************************
*********************** STATEFUL MEMORY  *********************************
*************************************************************************/
/*
   Current number of outstanding requests (queue length)
   at each node.
 */
register reg_queue_len {
    width: 16;
    instance_count: 32;
}
/*
   We need n sets of node load registers, where n is the
   max number of replicas.
*/
register reg_node_load_1 {
    width: 16;
    instance_count: 32;
}
register reg_node_load_2 {
    width: 16;
    instance_count: 32;
}
register reg_node_load_3 {
    width: 16;
    instance_count: 32;
}
register reg_node_load_4 {
    width: 16;
    instance_count: 32;
}
/*
   We need these id registers to find the node (among replicas)
   with the lowest load. register_hi is the id, and register_lo
   stores the node load. (We can't use reg_node_load again because
   each stateful alu can only output one field)
*/
register reg_node_id_1 {
    width: 64;
    instance_count: 32;
}
register reg_node_id_2 {
    width: 64;
    instance_count: 32;
}
register reg_node_id_3 {
    width: 64;
    instance_count: 32;
}
register reg_node_id_4 {
    width: 64;
    instance_count: 32;
}

register reg_min_node_load {
    // register_hi holds min_node, and register_lo holds min_node_load.
    width: 64;
    instance_count: 1;
}
register reg_rnode_1 {
    width: 8;
    instance_count: 32;
}
register reg_rnode_2 {
    width: 8;
    instance_count: 32;
}
register reg_rnode_3 {
    width: 8;
    instance_count: 32;
}
register reg_rnode_4 {
    width: 8;
    instance_count: 32;
}
/*************************************************************************
*********************** RESUBMIT  ****************************************
*************************************************************************/
field_list resubmit_fields {
    meta.tmp_node;
    meta.tmp_load;
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

@pragma stage 7
table tab_node_forward {
    reads {
        meta.tmp_node: exact;
    }
    actions {
        node_forward;
        _drop;
    }
    size: 32;
}

/*
   inc queue len
 */
blackbox stateful_alu sa_inc_queue_len {
    reg: reg_queue_len;
    update_lo_1_value: register_lo + 1;
    output_value: alu_lo;
    output_dst: meta.tmp_load;
}

action inc_queue_len() {
    sa_inc_queue_len.execute_stateful_alu(meta.tmp_node);
    resubmit(resubmit_fields);
}

@pragma stage 7
table tab_inc_queue_len {
    actions {
        inc_queue_len;
    }
    default_action: inc_queue_len;
    size: 1;
}

/*
   dec queue len
 */
blackbox stateful_alu sa_dec_queue_len {
    reg: reg_queue_len;
    condition_lo: register_lo > 1;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: register_lo - 1;
    output_value: alu_lo;
    output_dst: meta.tmp_load;
}

action dec_queue_len() {
    sa_dec_queue_len.execute_stateful_alu(meta.tmp_node);
    resubmit(resubmit_fields);
}

@pragma stage 7
table tab_dec_queue_len {
    actions {
        dec_queue_len;
    }
    default_action: dec_queue_len;
    size: 1;
}

/*
   copy header
 */
action copy_pegasus_header() {
    modify_field(meta.tmp_node, pegasus.node);
}

table tab_copy_pegasus_header {
    actions {
        copy_pegasus_header;
    }
    default_action: copy_pegasus_header;
    size: 1;
}

/*
   dummies
 */
blackbox stateful_alu sa_dummy_0 {
    reg: reg_min_node_load;
}

action dummy_0() {
    sa_dummy_0.execute_stateful_alu(pegasus.node);
}

table tab_dummy_0 {
    actions {
        dummy_0;
    }
    default_action: dummy_0;
    size: 1;
}

/*
   update min node load
*/
blackbox stateful_alu sa_update_min_node_load {
    reg: reg_min_node_load;
    condition_lo: meta.tmp_load < register_lo;
    condition_hi: meta.tmp_node == register_hi;
    update_lo_1_predicate: condition_lo or condition_hi;
    update_lo_1_value: meta.tmp_load;
    update_hi_1_predicate: condition_lo or condition_hi;
    update_hi_1_value: meta.tmp_node;
}

action update_min_node_load() {
    sa_update_min_node_load.execute_stateful_alu(0);
}

table tab_update_min_node_load {
    actions {
        update_min_node_load;
    }
    default_action: update_min_node_load;
    size: 1;
}

/*
   update node load (1-4)
*/
blackbox stateful_alu sa_update_node_load_1 {
    reg: reg_node_load_1;
    update_lo_1_value: meta.tmp_load;
}
blackbox stateful_alu sa_update_node_load_2 {
    reg: reg_node_load_2;
    update_lo_1_value: meta.tmp_load;
}
blackbox stateful_alu sa_update_node_load_3 {
    reg: reg_node_load_3;
    update_lo_1_value: meta.tmp_load;
}
blackbox stateful_alu sa_update_node_load_4 {
    reg: reg_node_load_4;
    update_lo_1_value: meta.tmp_load;
}

action update_node_load_1() {
    sa_update_node_load_1.execute_stateful_alu(meta.tmp_node);
}
action update_node_load_2() {
    sa_update_node_load_2.execute_stateful_alu(meta.tmp_node);
}
action update_node_load_3() {
    sa_update_node_load_3.execute_stateful_alu(meta.tmp_node);
}
action update_node_load_4() {
    sa_update_node_load_4.execute_stateful_alu(meta.tmp_node);
}

@pragma stage 2
table tab_update_node_load_1 {
    actions {
        update_node_load_1;
    }
    default_action: update_node_load_1;
    size: 1;
}
@pragma stage 3
table tab_update_node_load_2 {
    actions {
        update_node_load_2;
    }
    default_action: update_node_load_2;
    size: 1;
}
@pragma stage 4
table tab_update_node_load_3 {
    actions {
        update_node_load_3;
    }
    default_action: update_node_load_3;
    size: 1;
}
@pragma stage 5
table tab_update_node_load_4 {
    actions {
        update_node_load_4;
    }
    default_action: update_node_load_4;
    size: 1;
}

/*
   update node id (1-4)
*/
blackbox stateful_alu sa_update_node_id_1 {
    reg: reg_node_id_1;
    update_lo_1_value: meta.tmp_load;
}
blackbox stateful_alu sa_update_node_id_2 {
    reg: reg_node_id_2;
    update_lo_1_value: meta.tmp_load;
}
blackbox stateful_alu sa_update_node_id_3 {
    reg: reg_node_id_3;
    update_lo_1_value: meta.tmp_load;
}
blackbox stateful_alu sa_update_node_id_4 {
    reg: reg_node_id_4;
    update_lo_1_value: meta.tmp_load;
}

action update_node_id_1() {
    sa_update_node_id_1.execute_stateful_alu(meta.tmp_node);
}
action update_node_id_2() {
    sa_update_node_id_2.execute_stateful_alu(meta.tmp_node);
}
action update_node_id_3() {
    sa_update_node_id_3.execute_stateful_alu(meta.tmp_node);
}
action update_node_id_4() {
    sa_update_node_id_4.execute_stateful_alu(meta.tmp_node);
}

@pragma stage 2
table tab_update_node_id_1 {
    actions {
        update_node_id_1;
    }
    default_action: update_node_id_1;
    size: 1;
}
@pragma stage 3
table tab_update_node_id_2 {
    actions {
        update_node_id_2;
    }
    default_action: update_node_id_2;
    size: 1;
}
@pragma stage 4
table tab_update_node_id_3 {
    actions {
        update_node_id_3;
    }
    default_action: update_node_id_3;
    size: 1;
}
@pragma stage 5
table tab_update_node_id_4 {
    actions {
        update_node_id_4;
    }
    default_action: update_node_id_4;
    size: 1;
}

/*
   replicated keys
*/
blackbox stateful_alu sa_extract_min_node_load {
    reg: reg_min_node_load;
    output_value: register_hi;
    output_dst: meta.tmp_node;
}

action lookup_rkey(rkey_index) {
    sa_extract_min_node_load.execute_stateful_alu(0);
    modify_field(meta.rkey_index, rkey_index);
}

action set_default_dst_node() {
    bit_and(meta.tmp_node, pegasus.keyhash, HASH_MASK);
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
   extract rnode (1-4)
*/
blackbox stateful_alu sa_extract_rnode_1 {
    reg: reg_rnode_1;
    output_value: register_lo;
    output_dst: meta.rnode_1;
}
blackbox stateful_alu sa_extract_rnode_2 {
    reg: reg_rnode_2;
    output_value: register_lo;
    output_dst: meta.rnode_2;
}
blackbox stateful_alu sa_extract_rnode_3 {
    reg: reg_rnode_3;
    output_value: register_lo;
    output_dst: meta.rnode_3;
}
blackbox stateful_alu sa_extract_rnode_4 {
    reg: reg_rnode_4;
    output_value: register_lo;
    output_dst: meta.rnode_4;
}

action extract_rnode_1() {
    sa_extract_rnode_1.execute_stateful_alu(meta.rkey_index);
}
action extract_rnode_2() {
    sa_extract_rnode_2.execute_stateful_alu(meta.rkey_index);
}
action extract_rnode_3() {
    sa_extract_rnode_3.execute_stateful_alu(meta.rkey_index);
}
action extract_rnode_4() {
    sa_extract_rnode_4.execute_stateful_alu(meta.rkey_index);
}

table tab_extract_rnode_1 {
    actions {
        extract_rnode_1;
    }
    default_action: extract_rnode_1;
    size: 1;
}
table tab_extract_rnode_2 {
    actions {
        extract_rnode_2;
    }
    default_action: extract_rnode_2;
    size: 1;
}
table tab_extract_rnode_3 {
    actions {
        extract_rnode_3;
    }
    default_action: extract_rnode_3;
    size: 1;
}
table tab_extract_rnode_4 {
    actions {
        extract_rnode_4;
    }
    default_action: extract_rnode_4;
    size: 1;
}

/*
   find min rnode (1-4)
*/
blackbox stateful_alu sa_find_min_rnode_1 {
    reg: reg_node_load_1;
    output_value: register_lo;
    output_dst: meta.min_rload;
}
blackbox stateful_alu sa_find_min_rnode_2 {
    reg: reg_node_load_2;
    condition_lo: register_lo < meta.min_rload;
    output_predicate: condition_lo;
    output_value: register_lo;
    output_dst: meta.tmp_load;
}
blackbox stateful_alu sa_find_min_rnode_3_a {
    reg: reg_node_load_3;
    condition_lo: register_lo < meta.min_rload;
    output_predicate: condition_lo;
    output_value: register_lo;
    output_dst: meta.tmp_load;
}
blackbox stateful_alu sa_find_min_rnode_3_b {
    reg: reg_node_load_3;
    condition_lo: register_lo < meta.tmp_load;
    output_predicate: condition_lo;
    output_value: register_lo;
    output_dst: meta.tmp_load;
}
blackbox stateful_alu sa_find_min_rnode_4_a {
    reg: reg_node_load_4;
    condition_lo: register_lo < meta.min_rload;
    output_predicate: condition_lo;
    output_value: register_lo;
    output_dst: meta.tmp_load;
}
blackbox stateful_alu sa_find_min_rnode_4_b {
    reg: reg_node_load_4;
    condition_lo: register_lo < meta.tmp_load;
    output_predicate: condition_lo;
    output_value: register_lo;
    output_dst: meta.tmp_load;
}

action find_min_rnode_1() {
    sa_find_min_rnode_1.execute_stateful_alu(meta.rnode_1);
}
action find_min_rnode_2() {
    sa_find_min_rnode_2.execute_stateful_alu(meta.rnode_2);
}
action find_min_rnode_3_a() {
    sa_find_min_rnode_3_a.execute_stateful_alu(meta.rnode_3);
}
action find_min_rnode_3_b() {
    sa_find_min_rnode_3_b.execute_stateful_alu(meta.rnode_3);
}
action find_min_rnode_4_a() {
    sa_find_min_rnode_4_a.execute_stateful_alu(meta.rnode_4);
}
action find_min_rnode_4_b() {
    sa_find_min_rnode_4_b.execute_stateful_alu(meta.rnode_4);
}

@pragma stage 2
table tab_find_min_rnode_1 {
    actions {
        find_min_rnode_1;
    }
    default_action: find_min_rnode_1;
    size: 1;
}
@pragma stage 3
table tab_find_min_rnode_2 {
    actions {
        find_min_rnode_2;
    }
    default_action: find_min_rnode_2;
    size: 1;
}
@pragma stage 4
table tab_find_min_rnode_3_a {
    actions {
        find_min_rnode_3_a;
    }
    default_action: find_min_rnode_3_a;
    size: 1;
}
@pragma stage 4
table tab_find_min_rnode_3_b {
    actions {
        find_min_rnode_3_b;
    }
    default_action: find_min_rnode_3_b;
    size: 1;
}
@pragma stage 5
table tab_find_min_rnode_4_a {
    actions {
        find_min_rnode_4_a;
    }
    default_action: find_min_rnode_4_a;
    size: 1;
}
@pragma stage 5
table tab_find_min_rnode_4_b {
    actions {
        find_min_rnode_4_b;
    }
    default_action: find_min_rnode_4_b;
    size: 1;
}

/*
   find min rnode id (1-4)
*/
blackbox stateful_alu sa_find_min_rnode_id_1 {
    reg: reg_node_id_1;
    output_value: register_hi;
    output_dst: meta.tmp_node;
}
blackbox stateful_alu sa_find_min_rnode_id_2 {
    reg: reg_node_id_2;
    condition_lo: register_lo < meta.min_rload;
    output_predicate: condition_lo;
    output_value: register_hi;
    output_dst: meta.tmp_node_1;
}
blackbox stateful_alu sa_find_min_rnode_id_3_a {
    reg: reg_node_id_3;
    condition_lo: register_lo < meta.min_rload;
    output_predicate: condition_lo;
    output_value: register_hi;
    output_dst: meta.tmp_node_1;
}
blackbox stateful_alu sa_find_min_rnode_id_3_b {
    reg: reg_node_id_3;
    condition_lo: register_lo < meta.tmp_load;
    output_predicate: condition_lo;
    output_value: register_hi;
    output_dst: meta.tmp_node_1;
}
blackbox stateful_alu sa_find_min_rnode_id_4_a {
    reg: reg_node_id_4;
    condition_lo: register_lo < meta.min_rload;
    output_predicate: condition_lo;
    output_value: register_hi;
    output_dst: meta.tmp_node_1;
}
blackbox stateful_alu sa_find_min_rnode_id_4_b {
    reg: reg_node_id_4;
    condition_lo: register_lo < meta.tmp_load;
    output_predicate: condition_lo;
    output_value: register_hi;
    output_dst: meta.tmp_node_1;
}

action find_min_rnode_id_1() {
    sa_find_min_rnode_id_1.execute_stateful_alu(meta.rnode_1);
}
action find_min_rnode_id_2() {
    sa_find_min_rnode_id_2.execute_stateful_alu(meta.rnode_2);
}
action find_min_rnode_id_3_a() {
    sa_find_min_rnode_id_3_a.execute_stateful_alu(meta.rnode_3);
}
action find_min_rnode_id_3_b() {
    sa_find_min_rnode_id_3_b.execute_stateful_alu(meta.rnode_3);
}
action find_min_rnode_id_4_a() {
    sa_find_min_rnode_id_4_a.execute_stateful_alu(meta.rnode_4);
}
action find_min_rnode_id_4_b() {
    sa_find_min_rnode_id_4_b.execute_stateful_alu(meta.rnode_4);
}

@pragma stage 2
table tab_find_min_rnode_id_1 {
    actions {
        find_min_rnode_id_1;
    }
    default_action: find_min_rnode_id_1;
    size: 1;
}
@pragma stage 3
table tab_find_min_rnode_id_2 {
    actions {
        find_min_rnode_id_2;
    }
    default_action: find_min_rnode_id_2;
    size: 1;
}
@pragma stage 4
table tab_find_min_rnode_id_3_a {
    actions {
        find_min_rnode_id_3_a;
    }
    default_action: find_min_rnode_id_3_a;
    size: 1;
}
@pragma stage 4
table tab_find_min_rnode_id_3_b {
    actions {
        find_min_rnode_id_3_b;
    }
    default_action: find_min_rnode_id_3_b;
    size: 1;
}
@pragma stage 5
table tab_find_min_rnode_id_4_a {
    actions {
        find_min_rnode_id_4_a;
    }
    default_action: find_min_rnode_id_4_a;
    size: 1;
}
@pragma stage 5
table tab_find_min_rnode_id_4_b {
    actions {
        find_min_rnode_id_4_b;
    }
    default_action: find_min_rnode_id_4_b;
    size: 1;
}

/*
   copy load node (3-4)
*/
action copy_load_node() {
    modify_field(meta.min_rload, meta.tmp_load);
    modify_field(meta.tmp_node, meta.tmp_node_1);
}

table tab_copy_load_node_3 {
    actions {
        copy_load_node;
    }
    default_action: copy_load_node;
    size: 1;
}

table tab_copy_load_node_4 {
    actions {
        copy_load_node;
    }
    default_action: copy_load_node;
    size: 1;
}

table tab_copy_load_node_last {
    actions {
        copy_load_node;
    }
    default_action: copy_load_node;
    size: 1;
}

/*
   update rnode (1-4)
*/
blackbox stateful_alu sa_update_rnode_1 {
    reg: reg_rnode_1;
    update_lo_1_value: meta.tmp_node;
}
blackbox stateful_alu sa_update_rnode_2 {
    reg: reg_rnode_2;
    update_lo_1_value: RNODE_NONE;
}
blackbox stateful_alu sa_update_rnode_3 {
    reg: reg_rnode_3;
    update_lo_1_value: RNODE_NONE;
}
blackbox stateful_alu sa_update_rnode_4 {
    reg: reg_rnode_4;
    update_lo_1_value: RNODE_NONE;
}

action update_rnode_1() {
    sa_update_rnode_1.execute_stateful_alu(meta.rkey_index);
}
action update_rnode_2() {
    sa_update_rnode_2.execute_stateful_alu(meta.rkey_index);
}
action update_rnode_3() {
    sa_update_rnode_3.execute_stateful_alu(meta.rkey_index);
}
action update_rnode_4() {
    sa_update_rnode_4.execute_stateful_alu(meta.rkey_index);
}

table tab_update_rnode_1 {
    actions {
        update_rnode_1;
    }
    default_action: update_rnode_1;
    size: 1;
}
table tab_update_rnode_2 {
    actions {
        update_rnode_2;
    }
    default_action: update_rnode_2;
    size: 1;
}
table tab_update_rnode_3 {
    actions {
        update_rnode_3;
    }
    default_action: update_rnode_3;
    size: 1;
}
table tab_update_rnode_4 {
    actions {
        update_rnode_4;
    }
    default_action: update_rnode_4;
    size: 1;
}

/*
   debug
*/
action debug() {
    modify_field(pegasus.node, meta.tmp_node);
    modify_field(pegasus.load, meta.tmp_load);
}

table tab_debug {
    actions {
        debug;
    }
    default_action: debug;
    size: 1;
}

control process_resubmit {
    // stage 0
    apply(tab_update_min_node_load);
    // stage 2
    apply(tab_update_node_load_1);
    apply(tab_update_node_id_1);
    // stage 3
    apply(tab_update_node_load_2);
    apply(tab_update_node_id_2);
    // stage 4
    apply(tab_update_node_load_3);
    apply(tab_update_node_id_3);
    // stage 5
    apply(tab_update_node_load_4);
    apply(tab_update_node_id_4);
    // stage ?
    apply(tab_debug);
    if (pegasus.op == OP_REP) {
        apply(tab_l2_forward);
    } else {
        apply(tab_node_forward);
    }
}

control process_pegasus_reply {
    apply(tab_dummy_0);
    apply(tab_copy_pegasus_header);
    apply(tab_dec_queue_len);
}

control process_pegasus_request {
    // stage 0
    apply(tab_replicated_keys) {
        hit {
            if (pegasus.op == OP_GET) {
                // stage 1-6
                process_replicated_read();
            } else {
                // stage 1
                process_replicated_write();
            }
        }
    }
    // stage 7
    apply(tab_inc_queue_len);
}

control process_replicated_read {
    // stage 1
    apply(tab_extract_rnode_1);
    apply(tab_extract_rnode_2);
    apply(tab_extract_rnode_3);
    apply(tab_extract_rnode_4);
    // stage 2
    if (meta.rnode_1 != RNODE_NONE) {
        apply(tab_find_min_rnode_id_1);
        apply(tab_find_min_rnode_1);
    }
    // stage 3
    if (meta.rnode_2 != RNODE_NONE) {
        apply(tab_find_min_rnode_id_2);
        apply(tab_find_min_rnode_2);
    }
    // stage 4
    if (meta.rnode_3 != RNODE_NONE) {
        if (meta.tmp_load == 0) {
            apply(tab_find_min_rnode_id_3_a);
            apply(tab_find_min_rnode_3_a);
        } else {
            apply(tab_copy_load_node_3);
            apply(tab_find_min_rnode_id_3_b);
            apply(tab_find_min_rnode_3_b);
        }
    }
    // stage 5
    if (meta.rnode_4 != RNODE_NONE) {
        if (meta.tmp_load == 0) {
            apply(tab_find_min_rnode_id_4_a);
            apply(tab_find_min_rnode_4_a);
        } else {
            apply(tab_copy_load_node_4);
            apply(tab_find_min_rnode_id_4_b);
            apply(tab_find_min_rnode_4_b);
        }
    }
    // stage 6
    if (meta.tmp_load != 0) {
        apply(tab_copy_load_node_last);
    }
}

control process_replicated_write {
    // stage 1
    apply(tab_update_rnode_1);
    apply(tab_update_rnode_2);
    apply(tab_update_rnode_3);
    apply(tab_update_rnode_4);
}

control ingress {
    if (0 == ig_intr_md.resubmit_flag) {
        if (valid(pegasus)) {
            if (pegasus.op == OP_REP) {
                process_pegasus_reply();
            } else {
                process_pegasus_request();
            }
        } else {
            apply(tab_l2_forward);
        }
    } else {
        process_resubmit();
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control egress {
}
