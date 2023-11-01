#include "includes/defines.p4"
#include "includes/headers.p4"
#include "includes/parsers.p4"
#include "includes/checksum.p4"


#include "heavy_hitter.p4"
#include "ipv4.p4"
#include "ethernet.p4"

header_type nc_cache_md_t {
    fields {
        cache_exist: 1;
        cache_index: 14;
        cache_valid: 1;
    }
}
metadata nc_cache_md_t nc_cache_md;

// dependency marker @!slice, 0!@  @!position, control!@
action check_cache_exist_act(index) {
    modify_field (nc_cache_md.cache_exist, 1);
    modify_field (nc_cache_md.cache_index, index);
}
table check_cache_exist {
    reads {
        nc_hdr.key: exact;
    }
    actions {
        check_cache_exist_act;
    }
    size: NUM_CACHE;
}
// dependency marker @!end,0!@

register cache_valid_reg {
    width: 1;
    instance_count: NUM_CACHE;
}
// dependency marker @!slice, 1!@  @!position, control!@
action check_cache_valid_act() {
    register_read(nc_cache_md.cache_valid, cache_valid_reg, nc_cache_md.cache_index);
}
table check_cache_valid {
    actions {
        check_cache_valid_act;
    }
    //default_action: check_cache_valid_act;
}
// dependency marker @!end,1!@
action set_cache_valid_act() {
    register_write(cache_valid_reg, nc_cache_md.cache_index, 1);
}
table set_cache_valid {
    actions {
        set_cache_valid_act;
    }
    //default_action: set_cache_valid_act;
}

control process_cache {
    // dependency marker @!slice, 0!@ @!previous, none!@ @!position, control-apply!@
    // resource marker @!stage, 5!@ @!memory, 5!@
    // p4 marker @!metadata_in!@
    // p4 marker @!metadata_out!@
    apply (check_cache_exist);
    // dependency marker @!end,0!@

    // dependency marker @!slice,1!@ @!previous,0!@ @!position, control-apply!@
    // resource marker @!stage, 5!@ @!memory, 5!@
    // p4 marker @!metadata_in!@
    // p4 marker @!metadata_out!@
    if (nc_cache_md.cache_exist == 1) {
        if (nc_hdr.op == NC_READ_REQUEST) {
            apply (check_cache_valid);
        }
        else if (nc_hdr.op == NC_UPDATE_REPLY) {
            apply (set_cache_valid);
        }
    }
    // dependency marker @!end,1!@
}

#define HEADER_VALUE(i) \
    header_type nc_value_##i##_t { \
        fields { \
            value_##i##_1: 32; \
            value_##i##_2: 32; \
            value_##i##_3: 32; \
            value_##i##_4: 32; \
        } \
    } \
    header nc_value_##i##_t nc_value_##i;

#define PARSER_VALUE(i, ip1) \
    parser parse_nc_value_##i { \
        extract (nc_value_##i); \
        return parse_nc_value_##ip1; \
    }

#define REGISTER_VALUE_SLICE(i, j) \
    register value_##i##_##j##_reg { \
        width: 32; \
        instance_count: NUM_CACHE; \
    }

#define REGISTER_VALUE(i) \
    REGISTER_VALUE_SLICE(i, 1) \
    REGISTER_VALUE_SLICE(i, 2) \
    REGISTER_VALUE_SLICE(i, 3) \
    REGISTER_VALUE_SLICE(i, 4)

#define ACTION_READ_VALUE_SLICE(i, j) \
    action read_value_##i##_##j##_act() { \
        register_read(nc_value_##i.value_##i##_##j, value_##i##_##j##_reg, nc_cache_md.cache_index); \
    }

#define ACTION_READ_VALUE(i) \
    ACTION_READ_VALUE_SLICE(i, 1) \
    ACTION_READ_VALUE_SLICE(i, 2) \
    ACTION_READ_VALUE_SLICE(i, 3) \
    ACTION_READ_VALUE_SLICE(i, 4)

#define TABLE_READ_VALUE_SLICE(i, j) \
    table read_value_##i##_##j { \
        actions { \
            read_value_##i##_##j##_act; \
        } \
    }

#define TABLE_READ_VALUE(i) \
    TABLE_READ_VALUE_SLICE(i, 1) \
    TABLE_READ_VALUE_SLICE(i, 2) \
    TABLE_READ_VALUE_SLICE(i, 3) \
    TABLE_READ_VALUE_SLICE(i, 4)

#define ACTION_ADD_VALUE_HEADER(i) \
    action add_value_header_##i##_act() { \
        add_to_field(ipv4.totalLen, 16);\
        add_to_field(udp.len, 16);\
        add_header(nc_value_##i); \
    }

#define TABLE_ADD_VALUE_HEADER(i) \
    table add_value_header_##i { \
        actions { \
            add_value_header_##i##_act; \
        } \
    }

#define ACTION_WRITE_VALUE_SLICE(i, j) \
    action write_value_##i##_##j##_act() { \
        register_write(value_##i##_##j##_reg, nc_cache_md.cache_index, nc_value_##i.value_##i##_##j); \
    }

#define ACTION_WRITE_VALUE(i) \
    ACTION_WRITE_VALUE_SLICE(i, 1) \
    ACTION_WRITE_VALUE_SLICE(i, 2) \
    ACTION_WRITE_VALUE_SLICE(i, 3) \
    ACTION_WRITE_VALUE_SLICE(i, 4)

#define TABLE_WRITE_VALUE_SLICE(i, j) \
    table write_value_##i##_##j { \
        actions { \
            write_value_##i##_##j##_act; \
        } \
    }

#define TABLE_WRITE_VALUE(i) \
    TABLE_WRITE_VALUE_SLICE(i, 1) \
    TABLE_WRITE_VALUE_SLICE(i, 2) \
    TABLE_WRITE_VALUE_SLICE(i, 3) \
    TABLE_WRITE_VALUE_SLICE(i, 4)

#define ACTION_REMOVE_VALUE_HEADER(i) \
    action remove_value_header_##i##_act() { \
        subtract_from_field(ipv4.totalLen, 16);\
        subtract_from_field(udp.len, 16);\
        remove_header(nc_value_##i); \
    }

#define TABLE_REMOVE_VALUE_HEADER(i) \
    table remove_value_header_##i { \
        actions { \
            remove_value_header_##i##_act; \
        } \
    }

// dependency marker @!slice, 3!@  @!position, control!@
#define CONTROL_PROCESS_VALUE(i) \
    control process_value_##i { \
        if (nc_hdr.op == NC_READ_REQUEST and nc_cache_md.cache_valid == 1) { \
            apply (add_value_header_##i); \
            apply (read_value_##i##_1); \
            apply (read_value_##i##_2); \
            apply (read_value_##i##_3); \
            apply (read_value_##i##_4); \
        } \
        else if (nc_hdr.op == NC_UPDATE_REPLY and nc_cache_md.cache_exist == 1) { \
            apply (write_value_##i##_1); \
            apply (write_value_##i##_2); \
            apply (write_value_##i##_3); \
            apply (write_value_##i##_4); \
            apply (remove_value_header_##i); \
        } \
    }
// dependency marker @!end,3!@

#define HANDLE_VALUE(i, ip1) \
    HEADER_VALUE(i) \
    PARSER_VALUE(i, ip1) \
    REGISTER_VALUE(i) \
    ACTION_READ_VALUE(i) \
    TABLE_READ_VALUE(i) \
    ACTION_ADD_VALUE_HEADER(i) \
    TABLE_ADD_VALUE_HEADER(i) \
    ACTION_WRITE_VALUE(i) \
    TABLE_WRITE_VALUE(i) \
    ACTION_REMOVE_VALUE_HEADER(i) \
    TABLE_REMOVE_VALUE_HEADER(i) \
    CONTROL_PROCESS_VALUE(i)

#define FINAL_PARSER(i) \
    parser parse_nc_value_##i { \
        return ingress; \
    }

HANDLE_VALUE(1, 2)
HANDLE_VALUE(2, 3)
HANDLE_VALUE(3, 4)
HANDLE_VALUE(4, 5)
HANDLE_VALUE(5, 6)
HANDLE_VALUE(6, 7)
HANDLE_VALUE(7, 8)
HANDLE_VALUE(8, 9)
FINAL_PARSER(9)

header_type reply_read_hit_info_md_t {
    fields {
        ipv4_srcAddr: 32;
        ipv4_dstAddr: 32;
    }
}

metadata reply_read_hit_info_md_t reply_read_hit_info_md;

// dependency marker @!slice,2!@  @!position, control!@
action reply_read_hit_before_act() {
    modify_field (reply_read_hit_info_md.ipv4_srcAddr, ipv4.srcAddr);
    modify_field (reply_read_hit_info_md.ipv4_dstAddr, ipv4.dstAddr);
}

table reply_read_hit_before {
    actions {
        reply_read_hit_before_act;
    }
}
// dependency marker @!end,2!@

// dependency marker @!slice,4!@  @!position, control!@
action reply_read_hit_after_act() {
    modify_field (ipv4.srcAddr, reply_read_hit_info_md.ipv4_dstAddr);
    modify_field (ipv4.dstAddr, reply_read_hit_info_md.ipv4_srcAddr);
    modify_field (nc_hdr.op, NC_READ_REPLY);
}

table reply_read_hit_after {
    actions {
        reply_read_hit_after_act;
    }
}
// dependency marker @!end,4!@

control process_value {
    // dependency marker @!slice,2!@  @!previous,1!@ @!position, control!@
	// resource marker @!stage, 5!@ @!memory, 5!@
    // p4 marker @!metadata_in!@
    // p4 marker @!metadata_out!@
    if (nc_hdr.op == NC_READ_REQUEST and nc_cache_md.cache_valid == 1) {
        apply (reply_read_hit_before);
    }
    // dependency marker @!end,2!@

    // dependency marker @!slice,3!@  @!previous,2!@ @!position, control!@
	// resource marker @!stage, 5!@ @!memory, 5!@
    // p4 marker @!metadata_in!@
    // p4 marker @!metadata_out!@
    process_value_1();
    process_value_2();
    process_value_3();
    process_value_4();
    process_value_5();
    process_value_6();
    process_value_7();
    process_value_8();
    // dependency marker @!end,3!@

    // dependency marker @!slice,4!@  @!previous,3!@ @!position, control!@
	// resource marker @!stage, 5!@ @!memory, 5!@
    // p4 marker @!metadata_in!@
    // p4 marker @!metadata_out!@
    if (nc_hdr.op == NC_READ_REQUEST and nc_cache_md.cache_valid == 1) {
        apply (reply_read_hit_after);
    }
    // dependency marker @!end,4!@
}


control ingress {
    process_cache();
    process_value();

    apply (ipv4_route);
}

control egress {
    if (nc_hdr.op == NC_READ_REQUEST and nc_cache_md.cache_exist != 1) {
        heavy_hitter();
    }
    apply (ethernet_set_mac);
}
