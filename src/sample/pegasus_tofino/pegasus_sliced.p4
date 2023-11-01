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
#define OP_RC_REQ       0x5
#define OP_RC_ACK       0x6
#define OP_PUT_FWD      0x7

#define RKEY_NONE       0x7F
#define MAX_RKEY_RATE   0x7FFF

#define RSET_OP_NONE	0x0
#define RSET_OP_GET	0x1
#define RSET_OP_SET	0x2
#define RSET_OP_INSTALL	0x3

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
        client_id : 8;
        server_id : 8;
        load : 16;
        ver : 32;
        bitmap : 32;
    }
}

header pegasus_t pegasus;

header_type metadata_t {
    fields {
        rkey_index : 8;
        rset_size : 8;
        rset_index: 16;
        rset_offset : 16;
        node : 8;
        bitmap : 32;
        n_servers: 8;
        // requires initialization
        ver : 32;
        use_node_forward : 1;
	rset_op : 2;
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
    instance_count: 64;
}
/*
   version number of latest completed write
 */
register reg_rkey_ver_completed {
    width: 32;
    instance_count: 64;
}
/*
   rkey access rate counter
 */
register reg_rkey_rate_counter {
    width: 16;
    instance_count: 64;
}
/*
   round-robin counter
*/
register reg_rr_rkey {
    // per key counter
    width: 8;
    instance_count: 64;
}
register reg_rr_all_servers {
    width: 8;
    instance_count: 1;
}
register reg_n_servers {
    width: 8;
    instance_count: 1;
}
/*
    replica set
*/
register reg_rset_size {
    width: 8;
    instance_count: 64;
}
register reg_rset_bitmap {
    width: 32;
    instance_count: 64;
}
register reg_rset {
    width: 8;
    instance_count: 2048;
}
/*
   Read/Write ratio counter
 */
register reg_rkey_read_counter {
    width: 16;
    instance_count: 64;
}
register reg_rkey_write_counter {
    width: 16;
    instance_count: 64;
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
// dependency marker @!slice, 3!@  @!position, control!@
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
    size: 32;
}
// dependency marker @!end,3!@
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
   metadata initialization
*/
// dependency marker @!slice, 0!@  @!position, control!@
action meta_init() {
    modify_field(meta.use_node_forward, 0);
    modify_field(meta.rset_op, RSET_OP_NONE);
}

table tab_meta_init {
    actions {
        meta_init;
    }
    default_action: meta_init;
    size: 1;
}
// dependency marker @!end,0!@


// dependency marker @!slice, 1!@  @!position, control!@
/*
   replicated keys
*/
action is_rkey(rkey_index) {
    modify_field(meta.rkey_index, rkey_index);
}

action not_rkey() {
    modify_field(meta.rkey_index, RKEY_NONE);
}


table tab_replicated_keys {
    reads {
        pegasus.keyhash: exact;
    }
    actions {
        is_rkey;
        not_rkey;
    }
    default_action: not_rkey;
    size: 64;
}
// dependency marker @!end,1!@

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
blackbox stateful_alu sa_access_rr_rkey {
    reg: reg_rr_rkey;
    condition_lo: register_lo >= meta.rset_size - 1;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: 0;
    update_lo_2_predicate: not condition_lo;
    update_lo_2_value: register_lo + 1;
    output_value: alu_lo;
    output_dst: meta.rset_offset;
}
blackbox stateful_alu sa_access_rr_all_servers {
    reg: reg_rr_all_servers;
    condition_lo: register_lo >= meta.n_servers - 1;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: 0;
    update_lo_2_predicate: not condition_lo;
    update_lo_2_value: register_lo + 1;
    output_value: alu_lo;
    output_dst: meta.node;
}

action access_rr_rkey() {
    sa_access_rr_rkey.execute_stateful_alu(meta.rkey_index);
}
action access_rr_all_servers() {
    sa_access_rr_all_servers.execute_stateful_alu(0);
    modify_field(meta.use_node_forward, 1);
}

table tab_access_rr_rkey {
    actions {
        access_rr_rkey;
    }
    default_action: access_rr_rkey;
    size: 1;
}
table tab_access_rr_all_servers {
    actions {
        access_rr_all_servers;
    }
    default_action: access_rr_all_servers;
    size: 1;
}

/*
    get total number of servers
*/
blackbox stateful_alu sa_get_n_servers {
    reg: reg_n_servers;
    output_value: register_lo;
    output_dst: meta.n_servers;
}

action get_n_servers() {
    sa_get_n_servers.execute_stateful_alu(0);
}

table tab_get_n_servers {
    actions {
        get_n_servers;
    }
    default_action: get_n_servers;
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
    update_lo_1_value: register_lo + 1;
    output_value: register_lo;
    output_dst: meta.rset_offset;
}

// dependency marker @!slice, 1!@  @!position, control!@

action get_rset_size() {
    sa_get_rset_size.execute_stateful_alu(meta.rkey_index);
    modify_field(meta.rset_op, RSET_OP_GET);
}
action set_rset_size() {
    sa_set_rset_size.execute_stateful_alu(meta.rkey_index);
    modify_field(meta.rset_op, RSET_OP_SET);
}
action inc_rset_size() {
    sa_inc_rset_size.execute_stateful_alu(meta.rkey_index);
    modify_field(meta.rset_op, RSET_OP_INSTALL);
}

@pragma stage 3
table tab_get_rset_size {
    actions {
        get_rset_size;
    }
    default_action: get_rset_size;
    size: 1;
}
@pragma stage 3
table tab_set_rset_size {
    actions {
        set_rset_size;
    }
    default_action: set_rset_size;
    size: 1;
}
@pragma stage 3
table tab_inc_rset_size {
    actions {
        inc_rset_size;
    }
    default_action: inc_rset_size;
    size: 1;
}
// dependency marker @!end,1!@


/*
    bitmap
*/
blackbox stateful_alu sa_set_rset_bitmap {
    reg: reg_rset_bitmap;
    update_lo_1_value: pegasus.bitmap;
}
blackbox stateful_alu sa_insert_rset_bitmap {
    reg: reg_rset_bitmap;
    update_lo_1_value: register_lo | pegasus.bitmap;
    output_value: register_lo;
    output_dst: meta.bitmap;
}

action set_rset_bitmap() {
    sa_set_rset_bitmap.execute_stateful_alu(meta.rkey_index);
}
action insert_rset_bitmap() {
    sa_insert_rset_bitmap.execute_stateful_alu(meta.rkey_index);
    bit_and(meta.bitmap, meta.bitmap, pegasus.bitmap);
}

table tab_set_rset_bitmap {
    actions {
        set_rset_bitmap;
    }
    default_action: set_rset_bitmap;
    size: 1;
}
table tab_insert_rset_bitmap {
    actions {
        insert_rset_bitmap;
    }
    default_action: insert_rset_bitmap;
    size: 1;
}

// dependency marker @!slice, 1!@  @!position, control!@
/*
   calculate rset index
*/
action calc_rset_index(base) {
    add(meta.rset_index, meta.rset_offset, base);
}

table tab_calc_rset_index {
    reads {
        meta.rkey_index: exact;
    }
    actions {
        calc_rset_index;
    }
    default_action: calc_rset_index;
    size: 64;
}

/*
   get/set/install rset
 */
blackbox stateful_alu sa_get_rset {
    reg: reg_rset;
    output_value: register_lo;
    output_dst: meta.node;
}
blackbox stateful_alu sa_set_rset {
    reg: reg_rset;
    update_lo_1_value: pegasus.server_id;
}
blackbox stateful_alu sa_install_rset {
    reg: reg_rset;
    update_lo_1_value: pegasus.server_id;
}

action get_rset() {
    sa_get_rset.execute_stateful_alu(meta.rset_index);
    modify_field(meta.use_node_forward, 1);
}
action set_rset() {
    sa_set_rset.execute_stateful_alu(meta.rset_index);
}
action install_rset() {
    sa_install_rset.execute_stateful_alu(meta.rset_index);
}

table tab_get_rset {
    actions {
        get_rset;
    }
    default_action: get_rset;
    size: 1;
}
table tab_set_rset {
    actions {
        set_rset;
    }
    default_action: set_rset;
    size: 1;
}
table tab_install_rset {
    actions {
        install_rset;
    }
    default_action: install_rset;
    size: 1;
}
// dependency marker @!end,1!@
/*
   version number
 */
blackbox stateful_alu sa_get_ver_next {
    reg: reg_ver_next;
    update_lo_1_value: register_lo + 1;
    output_value: alu_lo;
    output_dst: pegasus.ver;
}
blackbox stateful_alu sa_check_rkey_ver_completed {
    reg: reg_rkey_ver_completed;
    condition_lo: pegasus.ver > register_lo;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: pegasus.ver;
    output_predicate: not condition_lo;
    output_value: register_lo;
    output_dst: meta.ver;
}

action get_ver_next() {
    sa_get_ver_next.execute_stateful_alu(meta.rkey_index);
}
action check_rkey_ver_completed() {
    sa_check_rkey_ver_completed.execute_stateful_alu(meta.rkey_index);
}

table tab_get_ver_next {
    actions {
        get_ver_next;
    }
    default_action: get_ver_next;
    size: 1;
}
table tab_check_rkey_ver_completed {
    actions {
        check_rkey_ver_completed;
    }
    default_action: check_rkey_ver_completed;
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
// dependency marker @!slice, 1!@  @!position, control!@
control process_reply {
    if (meta.rkey_index != RKEY_NONE) {
        apply(tab_check_rkey_ver_completed);
        if (meta.ver == 0) {
            apply(tab_set_rset_bitmap);
            apply(tab_set_rset_size);
        } else if (meta.ver == pegasus.ver) {
            apply(tab_insert_rset_bitmap);
            if (meta.bitmap == 0) {
                apply(tab_inc_rset_size);
            }
        }
    }
}


control process_request {
    if (meta.rkey_index != RKEY_NONE) {
        apply(tab_inc_rkey_rate_counter);
        apply(tab_get_n_servers);
        if (pegasus.op == OP_GET) {
            process_replicated_read();
        } else {
            process_replicated_write();
        }
    }
}


control process_replicated_read {
    apply(tab_inc_rkey_read_counter);
    apply(tab_get_rset_size);
    apply(tab_access_rr_rkey);
}

control process_replicated_write {
    apply(tab_inc_rkey_write_counter);
    apply(tab_get_ver_next);
    apply(tab_access_rr_all_servers);
}
// dependency marker @!end,1!@

control ingress {

    if (valid(pegasus)) {
        // dependency marker @!slice, 0!@ @!previous, none!@ @!position, control-apply!@
        // resource marker @!stage, 1!@ @!memory, 1!@
        // p4 marker @!metadata_in!@
        // p4 marker @!metadata_out!@
	      apply(tab_meta_init);
        // dependency marker @!end,0!@


        if (pegasus.op != OP_RC_REQ) {
        // dependency marker @!slice, 1!@ @!previous, 0!@ @!position, control-apply!@
        // resource marker @!stage, 4!@ @!memory, 4!@
        // p4 marker @!metadata_in, pegasus.op!@
        // p4 marker @!metadata_out, pegasus.op!@
            apply(tab_replicated_keys);
            if (pegasus.op == OP_REP_R or
                pegasus.op == OP_REP_W or
                pegasus.op == OP_RC_ACK) {
                process_reply();
            } else {
                process_request();
            }
            // dependency marker @!end,1!@

            // dependency marker @!slice, 2!@ @!previous, 1!@ @!position, control-apply!@
            // resource marker @!stage, 2!@ @!memory, 2!@
            // p4 marker @!metadata_in, meta.rset_op!@
            // p4 marker @!metadata_out, meta.rset_op!@
      	    if (meta.rset_op != RSET_OP_NONE) {
            		apply(tab_calc_rset_index);
            		if (meta.rset_op == RSET_OP_GET) {
            		    apply(tab_get_rset);
            		} else if (meta.rset_op == RSET_OP_SET) {
            		    apply(tab_set_rset);
            		} else {
            		    apply(tab_install_rset);
            	        }
            }
            // dependency marker @!end,2!@
        }

    }
    // dependency marker @!slice, 3!@ @!previous, 2!@ @!position, control-apply!@
    // resource marker @!stage, 1!@ @!memory, 1!@
    // p4 marker @!metadata_in!@
    // p4 marker @!metadata_out!@
    if (meta.use_node_forward != 0) {
        apply(tab_node_forward);
    } else {
        apply(tab_l2_forward);
    }
    // dependency marker @!end,2!@
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control egress {
}
