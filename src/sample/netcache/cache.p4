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
