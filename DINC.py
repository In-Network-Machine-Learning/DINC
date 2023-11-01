# This file is part of the Planter extend project: DINC.
# This program is a free software tool, which does ensemble in-network machine learning.
# licensed under Apache-2.0
#
# Copyright (c) 2020-2021 Changgang Zheng
# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford & YINS, Yale University
# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),
# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)

# =================== import needed pkgs ===================

import os
import json
import sys
import importlib.util
import platform
import argparse
import warnings
import networkx as nx
import time
import subprocess as sub
from multiprocessing import *
import signal
warnings.filterwarnings('ignore')

# =================== import DINC src ===================
# funtions
from src.functions.config_modification import *
from src.functions.input_CLI import *
from src.functions.figure_to_ASCII import *

def DINC():

    # =================== logo and copyright ===================

    print_logo()

    # =================== set argparse for DINC ===================

    parser = argparse.ArgumentParser(prog="Please use commend '-h' or '--help' for further information",
                                    usage='DINC can automatically generate distribute in-network computing algorithms',
                                    description='It is a on going work, if you find any bugs, please feel free to contact changgang.zheng@eng.ox.ac.uk, it is really important to us. Thank you.',
                                    epilog='Play happy with DINC ~')
    parser.add_argument("-m", "--manually_config", help="Manually config DINC or not? If not set, please config the following file <src/config/DINC_config.json>. If set, the DINC will ask you to input all the necessary configs.", action="store_true")
    parser.add_argument("-d", "--directory", type=str, help="In-network computing program directory", default = 'None')
    args = parser.parse_args()
    if args.manually_config:
        DINC_config = {}
    else:
        DINC_config = reload_DINC_config('src/configs/DINC_config.json')

    # =================== set DINC working directory in config ===================
    question = 'Where is your DINC folder?'
    default = os.getcwd()
    DINC_config = take_CLI_input(DINC_config, 'directory config', 'work', question, default, args.manually_config, True)

    # ====================== set network topology in config ======================
    question = 'Which network topology do you want to use?'
    default = 'Fat-Tree'
    DINC_config = take_CLI_input(DINC_config, 'network config', 'topology', question, default, args.manually_config, True, True, '/src/topologies')

    # dump the config file
    dump_DINC_config(DINC_config, 'src/configs/DINC_config.json')

    # =================== include model folder and files - table generator and table tester ===================
    network_topo_path = DINC_config['directory config']['work']+ '/src/topologies/' + DINC_config['network config']['topology']
    print('+ Add the following path: '+network_topo_path)
    sys.path.append(network_topo_path)
    # ran network topology
    model_main = importlib.util.spec_from_file_location("*", network_topo_path+"/network_topology.py")
    main_functions = importlib.util.module_from_spec(model_main)
    model_main.loader.exec_module(main_functions)
    Network_Topology = main_functions.generate_network_topology(args.manually_config)

    # Reload the config file to avoid overwrite
    DINC_config = reload_DINC_config('src/configs/DINC_config.json')

    # ==================== set p4 file directory in config ====================
    question = 'Where is your P4 file?'
    if args.directory == 'None':
        default = os.getcwd()+'/src/sample/Planter_DT/DT_performance_Iris.p4'
    else:
        default = args.directory
    DINC_config = take_CLI_input(DINC_config, 'directory config', 'p4 file', question, default, args.manually_config, True)

    # =================== set slicing setups in config =========================
    question = 'What method would you like to use to slice your P4 file?'
    default = 'Manually'
    DINC_config = take_CLI_input(DINC_config, 'p4 config', 'slicing method', question, default, args.manually_config, True, True, '/src/slicing')

    # dump the config file
    dump_DINC_config(DINC_config, 'src/configs/DINC_config.json')

    # =================== include model folder and files - p4 slicing and info extraction ===================
    slicing_module_path = DINC_config['directory config']['work'] + '/src/slicing/' + DINC_config['p4 config']['slicing method']
    print('+ Add the following path: ' + slicing_module_path)
    sys.path.append(slicing_module_path)
    # ran p4 slicing
    model_main = importlib.util.spec_from_file_location("*", slicing_module_path + "/p4_slicing.py")
    main_functions = importlib.util.module_from_spec(model_main)
    model_main.loader.exec_module(main_functions)
    P4_Information = main_functions.retrieve_p4_information(args.manually_config)

    # Reload the config file to avoid overwrite
    DINC_config = reload_DINC_config('src/configs/DINC_config.json')

    # =================== set solver setups in config =========================
    question = 'What solver would you like to use?'
    default = 'ILP'
    DINC_config = take_CLI_input(DINC_config, 'solver config', 'solver type', question, default, args.manually_config, True, True, '/src/solver')

    question = 'What variation of solver would you like to choose?'
    default = 'Type_1'
    DINC_config = take_CLI_input(DINC_config, 'solver config', 'solver variation', question, default, args.manually_config, True, True, '/src/solver/' + DINC_config['solver config']['solver type'])

    # dump the config file
    dump_DINC_config(DINC_config, 'src/configs/DINC_config.json')

    # =================== include model folder and files - p4 solver ===================
    solver_path = DINC_config['directory config']['work'] + '/src/solver/' + DINC_config['solver config']['solver type'] + '/' + DINC_config['solver config']['solver variation']
    print('+ Add the following path: ' + solver_path)
    sys.path.append(solver_path)
    # ran p4 solver
    model_main = importlib.util.spec_from_file_location("*", solver_path + "/do_optimization.py")
    main_functions = importlib.util.module_from_spec(model_main)
    model_main.loader.exec_module(main_functions)
    Allocation = main_functions.do_optimization(Network_Topology, P4_Information, args.manually_config)

    # Reload the config file to avoid overwrite
    DINC_config = reload_DINC_config('src/configs/DINC_config.json')

    # =================== generator setups in config for reconstruction =========================
    question = 'What generator would you like to use?'
    default = 'exact'
    DINC_config = take_CLI_input(DINC_config, 'p4 config', 'generator', question, default, args.manually_config, True, True, '/src/code_generator')
    DINC_config['p4 config']['begin test'] = "F"
    # dump the config file
    dump_DINC_config(DINC_config, 'src/configs/DINC_config.json')

    # =================== include model folder and files - p4 generator ===================
    generator_path = DINC_config['directory config']['work'] + '/src/code_generator/' + DINC_config['p4 config']['generator']
    print('+ Add the following path: ' + generator_path)
    sys.path.append(generator_path)
    # ran p4 slicing
    model_main = importlib.util.spec_from_file_location("*", generator_path + "/unified_generation_controller.py")
    main_functions = importlib.util.module_from_spec(model_main)
    model_main.loader.exec_module(main_functions)
    main_functions.generator(Allocation, P4_Information, Network_Topology, args.manually_config)
    print('- Remove the following path: ' + generator_path)
    sys.path.remove(generator_path)

    # =================== testing setups in config =========================
    DINC_config['p4 config']['begin test'] = "T"
    question = 'Would you like to test current strategy?'
    default = 'Y'
    DINC_config = take_CLI_input(DINC_config, 'test config', 'if test', question, default, args.manually_config)
    if DINC_config['test config']['if test'] != 'Y':
        exit()
        print("==============================================================================================\n"
              "=                                       Exiting DINC                                         =\n"
              "==============================================================================================")

    # =================== testing setups in config =========================
    question = 'What testing mode would you like to use?'
    default = 'BMv2'
    DINC_config = take_CLI_input(DINC_config, 'test config', 'targets', question, default, args.manually_config, True, True, '/src/test')

    # dump the config file
    dump_DINC_config(DINC_config, 'src/configs/DINC_config.json')

    # =================== include model folder and files - p4 testing ===================
    test_path = DINC_config['directory config']['work'] + '/src/test/' + DINC_config['test config']['targets']
    print('+ Add the following path: ' + test_path)
    sys.path.append(test_path)
    # ran p4 slicing
    model_main = importlib.util.spec_from_file_location("*", test_path + "/run_test.py")
    main_functions = importlib.util.module_from_spec(model_main)
    model_main.loader.exec_module(main_functions)
    main_functions.test_system(Allocation, P4_Information, Network_Topology, args.manually_config)




if __name__ == "__main__":
    try:
        DINC()
        print("==============================================================================================\n"
              "=                                       Exiting DINC                                         =\n"
              "==============================================================================================")
    except KeyboardInterrupt:
        print("==============================================================================================\n"
              "=                                       Exiting DINC                                         =\n"
              "==============================================================================================")


