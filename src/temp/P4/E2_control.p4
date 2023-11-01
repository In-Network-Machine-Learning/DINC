


    action write_default_class() {
        meta.result = 1;
    }

    action read_lable(bit<32> label){
        meta.result = label;
    }

    table decision {
        key = { meta.code_f0[0:0]:exact;
                meta.code_f1[1:0]:exact;
                meta.code_f2[2:0]:exact;
                meta.code_f3[2:0]:exact;
                }
        actions={
            read_lable;
            write_default_class;
        }
        size = 13;
        default_action = write_default_class;
    }
