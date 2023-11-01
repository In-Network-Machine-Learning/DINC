# This file is part of the Planter extend project: DINC.
# This program is a free software tool, which does ensemble in-network machine learning.
# licensed under Apache-2.0
#
# Copyright (c) 2020-2021 Changgang Zheng
# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford & Yale University
# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),
# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)
import json
import os
import time
import subprocess as sub

def run_command(command, root):
    sub.run(command, cwd = root)

def print_log_file(file_name):
    while True:
        if os.path.exists(file_name):
            time.sleep(1)
            break
    with open(file_name, 'r') as file:
        for i, line in enumerate(file.readlines()):
            print(line, end="")