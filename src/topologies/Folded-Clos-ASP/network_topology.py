# This file is part of the Planter project.
# This program is a free software tool, which does ensemble in-network machine learning.
# licensed under Apache-2.0
#
# Copyright (c) 2020-2021 Changgang Zheng
# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford
# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),
# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)
import copy

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from src.functions.input_CLI import *
from src.functions.config_modification import *


def generate_device_list(D, n_core, n_aggregation, n_access):
    idx = 0
    for c in range(n_core):
        D[idx] = [0, 'core', c] # layer ID, layer name, ID in this layer
        idx += 1
    for ag in range(n_aggregation):
        D[idx] = [1, 'aggregation', ag]
        idx += 1
    for ac in range(n_access):
        D[idx] = [2, 'access', ac]
        idx += 1
    return  D


def generate_adjacent_matrix(n_core, n_aggregation, n_access):
    #  ================ Generate Devices connection =============
    D = {}
    D = generate_device_list(D, n_core, n_aggregation, n_access)
    #  ================ Generate adjacent_matrix
    adjacent_matrix = np.zeros((len(D), len(D)))

    for x in range(len(D)):
        for y in range(len(D)):
            if abs(D[x][0] - D[y][0]) == 1:
                if x == y:
                    continue
                adjacent_matrix[x, y] = 1
    return D, adjacent_matrix


def device_list_to_path_reality(G, adjacent_matrix, in_device_list, out_device_list, DINC_config):
    number_devices = np.shape(adjacent_matrix)[0]
    P = {}
    path_idx = 0
    for i in in_device_list:
        for o in out_device_list:

            if i == o:
                continue
            for path in nx.all_shortest_paths(G, source=i, target=o):
                if len(path)==5:
                    if list(set(range(DINC_config['network config']['n_core'])).intersection(path)):
                        # print('- have core',list(set(range(DINC_config['network config']['n_core'])).intersection(path)), path)
                        if path[0]>=DINC_config['network config']['n_core']:
                            # print('selected')
                            P[path_idx] = path
                            path_idx += 1
                    # else:
                    #     print('- no core',list(set(range(DINC_config['network config']['n_core'])).intersection(path)))
                elif len(path)<=3:
                    P[path_idx] = path
                    path_idx += 1
                # print(path)
            # P, path_idx, _ = device_list_to_path_solver(P, adjacent_matrix, i, o, path_idx, [i], number_devices, True)
    return P


def generate_network_topology(manually_config=True):
    DINC_config = reload_DINC_config('src/configs/DINC_config.json')

    # =================== set DINC network config: spine number ===================
    question = 'How many switches do we used for core layer?'
    default = 40
    DINC_config = take_CLI_input(DINC_config, 'network config', 'n_core', question, default, manually_config,
                                 numeric=True)

    # =================== set DINC network config: aggregation number ===================
    question = 'How many switches do we used for aggregation layer?'
    default = 80
    DINC_config = take_CLI_input(DINC_config, 'network config', 'n_aggregation', question, default, manually_config,
                                 numeric=True)
    # =================== set DINC network config: rack number ===================
    question = 'How many switches do we used for access layer?'
    default = 256
    DINC_config = take_CLI_input(DINC_config, 'network config', 'n_access', question, default, manually_config,
                                 numeric=True)


    n_core = DINC_config['network config']['n_core']
    n_aggregation = DINC_config['network config']['n_aggregation']
    n_access = DINC_config['network config']['n_access']
    Network_Topology = {}

    Network_Topology['device_list'], Network_Topology['adjacent_matrix'] = generate_adjacent_matrix(n_core, n_aggregation, n_access)

    adjacent_matrix = Network_Topology['adjacent_matrix']

    # from adjacent matrix to graph
    Network_Graph = nx.DiGraph()
    for i in range(np.shape(adjacent_matrix)[0]):
        for j in range(np.shape(adjacent_matrix)[1]):
            if adjacent_matrix[i][j] == 1:
                Network_Graph.add_edge(i, j)
    Network_Topology['Graph'] = Network_Graph

    nx.draw(Network_Graph, with_labels=True, node_size=500, node_color="skyblue", node_shape="o", alpha=0.5,
            linewidths=5)
    DINC_config['directory config']['log plot file name'] = DINC_config['network config']['topology'] + '_' + str(
        DINC_config['network config']['n_core']) + 'core_' + str(
        DINC_config['network config']['n_aggregation']) + 'aggregation_' + str(
        DINC_config['network config']['n_access']) + 'access.pdf'
    log_dir = './src/logs/network_topology_' + DINC_config['directory config']['log plot file name']
    plt.savefig(log_dir, dpi=600, format='pdf', bbox_inches='tight')

    # =================== plot the generated network topology? ===================
    question = 'If you want to display your network topology?'
    default = False
    DINC_config = take_CLI_input(DINC_config, 'operation config', 'display plot', question, default, manually_config)
    if DINC_config['operation config']['display plot'] == True:
        plt.show()
    plt.close()

    # ======================= set input devices in config =======================
    question = 'Which are input devices (please check the reference graph in the previous step)?'
    default = '[2, 3, 5, 6]'
    DINC_config = take_CLI_input(DINC_config, 'network config', 'input device list', question, default, manually_config)
    DINC_config['network config']['input device list'] = str_to_array(
        DINC_config['network config']['input device list'])
    Network_Topology['input device list'] = DINC_config['network config']['input device list']
    in_device_list = Network_Topology['input device list']
    # ======================= set input devices in config =======================
    question = 'Which are output devices (please check the reference graph in the previous step)?'
    default = '[0]'
    DINC_config = take_CLI_input(DINC_config, 'network config', 'output device list', question, default,
                                 manually_config)
    DINC_config['network config']['output device list'] = str_to_array(
        DINC_config['network config']['output device list'])
    Network_Topology['output device list'] = DINC_config['network config']['output device list']
    out_device_list = Network_Topology['output device list']

    # ========= input devices resource =========
    question = 'Which resources should be considered?'
    default = '[stage, memory]'
    DINC_config = take_CLI_input(DINC_config, 'network config', 'resources list', question, default, manually_config,
                                 numeric=False)
    DINC_config['network config']['resources list'] = str_to_array(DINC_config['network config']['resources list'],
                                                                   margine=1)
    Network_Topology['resources list'] = DINC_config['network config']['resources list']

    # ========= devices resource =========
    for resource in DINC_config['network config']['resources list']:
        question = 'Which resources should be considered?'
        default = str((5 * np.ones(len(Network_Topology['device_list']))).astype(int).tolist())
        DINC_config = take_CLI_input(DINC_config, 'network config', resource, question, default, manually_config,
                                     numeric=False)
        DINC_config['network config'][resource] = str_to_array(DINC_config['network config'][resource], margine=1)
        Network_Topology[resource] = DINC_config['network config'][resource]

    # dump the config file
    dump_DINC_config(DINC_config, 'src/configs/DINC_config.json')

    P = device_list_to_path_reality(Network_Graph, adjacent_matrix, in_device_list, out_device_list, DINC_config)
    Network_Topology['Path'] = copy.deepcopy(P)

    #  test ====================================
    Test_Network_Topology = {}
    for keys in Network_Topology.keys():
        if keys == 'Graph':
            continue
        Test_Network_Topology[keys] = copy.deepcopy(Network_Topology[keys])
    dump_DINC_config(Test_Network_Topology, 'src/configs/Network_Topology.json')
    #  test ====================================

    return Network_Topology