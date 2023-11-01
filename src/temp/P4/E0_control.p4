    action extract_feature0(out bit<1> meta_code, bit<1> tree){
        meta_code = tree;
    }
    action extract_feature1(out bit<2> meta_code, bit<2> tree){
        meta_code = tree;
    }





    table lookup_feature0 {
        key = { meta.feature0:ternary; }
        actions = {
            extract_feature0(meta.code_f0);
            NoAction;
            }
        size = 8;
        default_action = NoAction;
    }

    table lookup_feature1 {
        key = { meta.feature1:ternary; }
        actions = {
            extract_feature1(meta.code_f1);
            NoAction;
            }
        size = 7;
        default_action = NoAction;
    }
