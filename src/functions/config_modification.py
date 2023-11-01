# This file is part of the Planter extend project: DINC.
# This program is a free software tool, which does ensemble in-network machine learning.
# licensed under Apache-2.0
#
# Copyright (c) 2020-2021 Changgang Zheng
# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford & Yale University
# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),
# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)

import os
import json
from src.functions.json_encoder import *

def reload_DINC_config(config_file_dir):
    if os.path.exists(config_file_dir):
        DINC_config = json.load(open(config_file_dir, 'r'))
    else:
        DINC_config = {}
    return DINC_config


def dump_DINC_config(DINC_config, config_file_dir, print_log = False):
    json.dump(DINC_config, open(config_file_dir, 'w'), indent=4, cls=NpEncoder)
    if print_log:
        print('Dump the targets info to '+config_file_dir)