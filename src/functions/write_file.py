# This file is part of the Planter project.
# This program is a free software tool, which does ensemble in-network machine learning.
# licensed under Apache-2.0
#
# Copyright (c) 2020-2021 Changgang Zheng
# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford
# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),
# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)

import os
import glob
from src.functions.add_license import *

def open_new_file(fname):
    with open(fname, 'w') as file:
        file.write("")

def write_line(line, file_name, first_line_of_file = False, add_license_txt = False):
    if first_line_of_file:
        open_new_file(file_name)
    if add_license_txt:
        add_license(file_name, first_line = first_line_of_file)
    with open(file_name, 'a') as file:
        file.write(line)

def clean_dir(dir, type = '.p4'):
    files = glob.glob(dir+'/*'+type, recursive=True)
    for f in files:
        try:
            print('- Remove file: '+f)
            os.remove(f)
        except OSError as e:
            print("Error: %s : %s" % (f, e.strerror))


def write_p4_file_with_space(p4_file_name, before_p4_leading_space, space_gap, target_file):
    with open(p4_file_name, 'r') as file:
        First_Line = True
        for line_idx, line in enumerate(file.readlines()):
            # if 'default_class' in line:
            #     pass
            if First_Line:
                p4_leading_space = len(line) - len(line.lstrip(' '))
                extra_space = space_gap + before_p4_leading_space - p4_leading_space
                if len(set(line)) > 1:
                    First_Line = False
            # if extra_space == 4:
            #     pass

            # print(extra_space, space_gap, before_p4_leading_space, p4_leading_space)
            # print(line)
            if extra_space < 0:
                target_file.write(line[abs(extra_space):])
            else:
                target_file.write(extra_space * ' ' + line)