# This file is part of the Planter extend project: DINC.
# This program is a free software tool, which does ensemble in-network machine learning.
# licensed under Apache-2.0
#
# Copyright (c) 2020-2021 Changgang Zheng
# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford & Yale University
# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),
# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)

import sys
import os
import json
import shutil
import importlib.util
import stat
import networkx as nx
import copy
import numpy as np
import platform
import getpass
from multiprocessing import *
from src.functions.config_modification import *
from src.functions.write_file import *
from src.functions.json_encoder import *
from src.functions.input_CLI import *
from src.functions.cmd_related import *

def id_to_ip(id):
    if id == 0:
        id = 254
    if id >= 2**8:
        print("Error, ip address is not enough! Please change the id_to_ip function.")
        exit()
    else:
        ip = "10.0.0.%d" % int(id)
        return ip

def id_to_mac(id):
    if id >= 2 ** 8:
        print("Error, mac address is not enough! Please change the id_to_ip function.")
        exit()
    else:
        mac = '10:00:00:00:00:%02x' % int(id)
        return mac

def id_port_to_mac(id, port):
    if id >= 2 ** 8:
        print("Error, mac address is not enough! Please change the id_to_ip function.")
        exit()
    else:
        mac = 'c8:00:00:00:%02x' % int(port) + ':%02x' % int(id)
        return mac


def generate_command_file(BMv2_network_config, file_dir):
    # dir = '../DINC_multi_prog/commands/'
    for s in BMv2_network_config['switch id']:
        file_name = file_dir + 's' + str(s) + '.txt'
        # add_license(fname)
        with open(file_name, 'w') as command:
            for rt_idx in BMv2_network_config['Routing']['switch'][int(s)]['routing table']:
                ip = BMv2_network_config['Routing']['switch'][int(s)]['routing table'][rt_idx][0]
                port = str(BMv2_network_config['Routing']['switch'][int(s)]['routing table'][rt_idx][1])
                mac = BMv2_network_config['Routing']['switch'][int(s)]['routing table'][rt_idx][2]
                command.write('table_add SwitchIngress.ipv4_lpm SwitchIngress.ipv4_forward ' + ip + '/32 => ' + mac + ' ' + port + '\n')
        os.chmod(file_name, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

def generate_insert_rules_command(BMv2_network_config, file_name, default_thrift_port = 9090):
    # file_name = '../DINC_multi_prog/insert_rules.sh'
    # add_license(fname)
    with open(file_name, 'w') as command:
        for s in BMv2_network_config['switch id']:
            thrift_port = str(default_thrift_port + int(s))
            command.write('simple_switch_CLI --thrift-port ' + thrift_port + ' < ./commands/s' + str(s) + '.txt\n')
    os.chmod(file_name, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)


def generate_run_demo_command(BMv2_network_config, BMv2_path, password, file_name):
    # file_name = '../DINC_multi_prog/insert_rules.sh'
    # add_license(fname)
    with open(file_name, 'w') as command:
        command.write("#!/bin/bash\n"
                      "BMV2_PATH=" + BMv2_path + "\n"
                      "SWITCH_PATH=$BMV2_PATH/targets/simple_switch/simple_switch\n"
                      "echo '"+password+"' | sudo -S $SWITCH_PATH >/dev/null 2>&1\n"
                      "sudo make clean\n"
                      "sudo PYTHONPATH=$PYTHONPATH:$BMV2_PATH/mininet/ python3 main.py --behavioral-exe $SWITCH_PATH\n")
    os.chmod(file_name, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)


# def generate_run_demo_command(BMv2_network_config, BMv2_path, file_name):
#     # file_name = '../DINC_multi_prog/insert_rules.sh'
#     # add_license(fname)
#     with open(file_name, 'w') as command:
#         command.write("#!/bin/bash\n"
#                       "BMV2_PATH=" + BMv2_path + "\n"
#                       "SWITCH_PATH=$BMV2_PATH/targets/simple_switch/simple_switch\n"
#                       "sudo $SWITCH_PATH >/dev/null 2>&1\n"
#                       "sudo make clean\n"
#                       "sudo PYTHONPATH=$PYTHONPATH:$BMV2_PATH/mininet/ python3 main.py --behavioral-exe $SWITCH_PATH\n")
#     os.chmod(file_name, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)



def test_system(Allocation, P4_Information, Network_Topology, manually_config = True):
    DINC_config = reload_DINC_config('src/configs/DINC_config.json')
    # DINC_config['network config']['architectures'][3] = 'v2model'
    # if len(set(DINC_config['network config']['architectures'])) == 1 and DINC_config['network config']['architectures'][0] == 'v1model':
    #     pass
    # else:
    print('All P4 files will be regenerated with v1model architecture to meet the testing environment requirements!')
    generator_path = DINC_config['directory config']['work'] + '/src/code_generator/' + 'v1model'
    print('Add the following path: ' + generator_path)
    sys.path.append(generator_path)
    # ran p4 slicing
    model_main = importlib.util.spec_from_file_location("*", generator_path + "/unified_generation_controller.py")
    main_functions = importlib.util.module_from_spec(model_main)
    model_main.loader.exec_module(main_functions)
    main_functions.generator(Allocation, P4_Information, Network_Topology, manually_config)
    print('Remove the following path: ' + generator_path)
    sys.path.remove(generator_path)
    print("P4 Generation Finished")

    # =================== set DINC working directory in config ===================
    question = 'Where is your BMv2 folder?'
    default = '/home/jesu3779/mysde/behavioral-model-1.15.0'
    DINC_config = take_CLI_input(DINC_config, 'directory config', 'BMv2', question, default, manually_config, True)
    dump_DINC_config(DINC_config, 'src/configs/DINC_config.json')
    BMv2_path = DINC_config['directory config']['BMv2']

    adjacent_matrix = Network_Topology['adjacent_matrix']
    Network_Graph = Network_Topology['Graph']
    BMv2_network_config = {}
    BMv2_network_config['switch to server'] = list(set(np.sort(Network_Topology['input device list'] + Network_Topology['output device list'])))
    BMv2_network_config['switch id'] = list(Network_Topology['device_list'].keys())

    BMv2_network_config['switch to switch'] = {}
    BMv2_network_config['switch port'] = {}
    BMv2_network_config['switch to switch inverse'] = {}
    idx = 0
    switch_port_count = np.ones(len(list(Network_Topology['device_list'].keys())))
    for i in range(np.shape(adjacent_matrix)[0]):
        for j in range(i, np.shape(adjacent_matrix)[1]):
            if adjacent_matrix[i][j] == 1:
                BMv2_network_config['switch to switch'][idx] = [i, j]
                BMv2_network_config['switch port'][idx] = [int(switch_port_count[i]), int(switch_port_count[j])]
                BMv2_network_config['switch to switch inverse'][str([i, j])] = idx
                switch_port_count[i] += 1
                switch_port_count[j] += 1
                idx += 1

    BMv2_network_config['switch to P4 file'] = {}
    idx = 0
    for d in BMv2_network_config['switch id']:
        file_name = 's' + str(d) + '.p4'
        p4_file ='./P4/' + file_name
        BMv2_network_config['switch to P4 file'][idx] = p4_file
        idx += 1

    BMv2_network_config['Routing'] = {}
    BMv2_network_config['Routing']['server'] = {}
    for h in BMv2_network_config['switch to server']:
        BMv2_network_config['Routing']['server'][int(h)] = {}
    BMv2_network_config['Routing']['switch'] = {}
    for s in BMv2_network_config['switch id']:
        BMv2_network_config['Routing']['switch'][int(s)] = {}
        # BMv2_network_config['Routing']['server'][int(id)]['mac'] = []
        BMv2_network_config['Routing']['switch'][int(s)]['num of table entries'] = 0
        BMv2_network_config['Routing']['switch'][int(s)]['routing table'] = {}

    std_to_host_port = 88
    std_host_departure_port = 80
    for id in BMv2_network_config['switch id']:
        if int(id) in BMv2_network_config['switch to server']:
            BMv2_network_config['Routing']['server'][int(id)]['ip'] = id_to_ip(int(id))  # can be replaced by id to ip function in the future
            BMv2_network_config['Routing']['server'][int(id)]['mac'] = id_to_mac(int(id))  # can be replaced by id to mac function in the future
            BMv2_network_config['Routing']['server'][int(id)]['port'] = std_to_host_port  # can be replaced by id to port function in the future
            BMv2_network_config['Routing']['server'][int(id)]['num of table entries'] = 0
            BMv2_network_config['Routing']['server'][int(id)]['routing table'] = {}

    for h_init in BMv2_network_config['switch to server']:
        for h_target in BMv2_network_config['switch to server']:
            num = copy.deepcopy(BMv2_network_config['Routing']['server'][h_init]['num of table entries'])
            std_first_hop_switch_mac = id_port_to_mac(h_init, std_to_host_port)
            BMv2_network_config['Routing']['server'][h_init]['routing table'][num] = [
                BMv2_network_config['Routing']['server'][h_target]['ip'], std_host_departure_port,
                std_first_hop_switch_mac]
            BMv2_network_config['Routing']['server'][h_init]['num of table entries'] += 1

    for id in BMv2_network_config['switch id']:
        d = int(id)
        for h in BMv2_network_config['switch to server']:
            if d != h:
                next_hop_switch = nx.shortest_path(Network_Graph, source=d, target=h)[1]
                switch_key = str([d, next_hop_switch])
                if switch_key in BMv2_network_config['switch to switch inverse'].keys():
                    port_idx = BMv2_network_config['switch to switch inverse'][switch_key]
                    port = BMv2_network_config['switch port'][port_idx][0]
                    port_for_next_hop_switch = BMv2_network_config['switch port'][port_idx][1]
                else:
                    inverse_awitch_key = str([next_hop_switch, d])
                    port_idx = BMv2_network_config['switch to switch inverse'][inverse_awitch_key]
                    port = BMv2_network_config['switch port'][port_idx][1]
                    port_for_next_hop_switch = BMv2_network_config['switch port'][port_idx][0]
                num = copy.deepcopy(BMv2_network_config['Routing']['switch'][d]['num of table entries'])
                mac = id_port_to_mac(next_hop_switch, port_for_next_hop_switch)
                BMv2_network_config['Routing']['switch'][d]['routing table'][num] = [
                    BMv2_network_config['Routing']['server'][h]['ip'], port, mac]
                BMv2_network_config['Routing']['switch'][d]['num of table entries'] += 1
            else:
                mac = id_to_mac(h)
                num = copy.deepcopy(BMv2_network_config['Routing']['switch'][d]['num of table entries'])
                BMv2_network_config['Routing']['switch'][d]['routing table'][num] = [
                    BMv2_network_config['Routing']['server'][h]['ip'], std_to_host_port, mac]
                BMv2_network_config['Routing']['switch'][d]['num of table entries'] += 1

    work_root = DINC_config['directory config']['work']+'/src/test/' + DINC_config['test config']['targets'] + '/test_environment'
    sudo_password= getpass.getpass("- Please input your password for 'sudo' command: ") or 'jesu3779'
    dump_DINC_config(BMv2_network_config, work_root + '/temp/BMv2_network_config.json', True)
    run_demo_command = work_root + '/run_demo.sh'
    generate_run_demo_command(BMv2_network_config, BMv2_path, sudo_password, run_demo_command)
    insert_rules_command = work_root + '/insert_rules.sh'
    generate_insert_rules_command(BMv2_network_config, insert_rules_command)
    file_dir = work_root + '/commands/'
    generate_command_file(BMv2_network_config, file_dir)
    print("+ Test scripts are generated!")

    if platform.system() != 'Linux':
        print(
            'Your system is ' + platform.system() + ' but not linux, pleasse make sure bmv2, p4c and mininet is installed on your os.')
        exit()

    processes = []
    # =================== test the switch model ===================
    run_demo_root = work_root
    task1_run_demo = Process(target=run_command, args=(str(run_demo_command), str(run_demo_root),))
    task1_run_demo.daemon = True
    task1_run_demo.start()
    processes.append(task1_run_demo)

    print('Join all subprocess together ...')
    try:
        for p in processes:
            p.join()
    except Exception as e:
        print(str(e))
