# This file is part of the Planter project.
# This program is a free software tool, which does ensemble in-network machine learning.
# licensed under Apache-2.0
#
# Copyright (c) 2020-2021 Changgang Zheng
# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford
# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),
# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)

import os

def find_folder_options(f):
    fs = os.listdir(f)
    print("  What option is available: ",end="")
    first = True
    for f1 in fs:
        tmp_path = os.path.join(f, f1)
        if os.path.isdir(tmp_path):
            if "__" not in f1:
                if first:
                    print(f1,end="")
                    first=False
                else:
                    print(", "+f1,end="")
    print(".")


def find_file_options(f):
    fs = os.listdir(f)
    print("  What option is available: ",end="")
    first = True
    for f1 in fs:
        tmp_path = os.path.join(f, f1)
        if not os.path.isdir(tmp_path):
            if first:
                print(f1,end="")
                first=False
            else:
                print(", "+f1,end="")
    print(" ")



