def add_license(fname, first_line = True):
    if first_line:
        operation = 'w'
    else:
        operation = 'a'
    with open(fname, operation) as file:
        file.write("########################################################################\n" 
                   "# This program is a free software tool, which does ensemble in-network machine learning.\n" 
                   "# licensed under Apache-2.0\n" 
                   "#\n" 
                   "# Copyright (c) 2020-2021 Changgang Zheng\n" 
                   "# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford & YINS, Yale University\n" 
                   "# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),\n" 
                   "# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)\n" 
                   "#########################################################################\n" 
                   "# This file was autogenerated\n\n"
                   )