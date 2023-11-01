


    action extract_feature2(out bit<3> meta_code, bit<3> tree){
        meta_code = tree;
    }

    action extract_feature3(out bit<3> meta_code, bit<3> tree){
        meta_code = tree;
    }


    table lookup_feature2 {
        key = { meta.feature2:ternary; }
        actions = {
            extract_feature2(meta.code_f2);
            NoAction;
            }
        size = 15;
        default_action = NoAction;
    }

    table lookup_feature3 {
        key = { meta.feature3:ternary; }
        actions = {
            extract_feature3(meta.code_f3);
            NoAction;
            }
        size = 10;
        default_action = NoAction;
    }

