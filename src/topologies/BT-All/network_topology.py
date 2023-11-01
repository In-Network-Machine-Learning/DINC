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
import csv, requests, time
import matplotlib.pyplot as plt
from src.functions.input_CLI import *
from src.functions.config_modification import *

def Plot_BT():
    import pandas as pd
    pass

def generate_device_list(D):


    Node_id_str = []
    Node_level = []
    edges = []
    weight = []
    North = []
    East = []

    # opening the nodes.csv file
    with open('/Users/changgang/Documents/GitHub/Data/BT/BTTopolgyFiles/nodes.csv', mode='r') as file:

        csvFile = csv.reader(file)
        for lines in csvFile:
            # Remove macro cell and msan nodes (to reduce the topology)
            if lines[25] != "macro cell" and lines[25] != "msan":
                Node_id_str.append(lines[16])
                Node_level.append(lines[25])
                East.append(lines[3])
                North.append(lines[6])
        del Node_id_str[0]
        del Node_level[0]
        del East[0]
        del North[0]

    # opening the edges.csv file
    with open('/Users/changgang/Documents/GitHub/Data/BT/BTTopolgyFiles/edges.csv', mode='r') as file:

        csvFile = csv.reader(file)
        i = 0
        for lines in csvFile:
            # Also remove the edges connected to macro cell and msan nodes
            if i == 0 or lines[2] == "macro cell" or lines[15] == "macro cell" or lines[2] == "msan" or lines[
                15] == "msan":
                i = 1
                continue

            FromNode = Node_id_str.index(lines[3])
            ToNode = Node_id_str.index(lines[16])

            inverse_tuple = [ToNode, FromNode]
            # Remove duplicate edges
            if inverse_tuple in edges:
                continue

            if lines[2] == "inner core" or lines[2] == "outer core" or lines[15] == "inner core" or lines[
                15] == "outer core":
                weight.append(10)  # the bandwidth of the links can be changed as desired
            elif lines[2] == "metro" or lines[2] == "metro":
                weight.append(10)
            elif lines[2] == "tier_1" or lines[2] == "tier_1":
                weight.append(2.5)
            elif lines[2] == "msan" or lines[2] == "msan":
                weight.append(1)

            edges.append([FromNode, ToNode])

    # with open("/Users/changgang/Documents/GitHub/Data/BT/BTTopolgyFiles/BT.txt", "w") as file:

    # print(str(len(Node_id_str)) + "    " + str(len(edges)) + "")
    # print("===================")
    d_inx = 0
    for i in range(len(Node_id_str)):
        # print(str(i) + "")
        D[d_inx] = {}
        D[d_inx]['BT ID'] = Node_id_str[i]
        D[d_inx]['N'] = int(float(North[i]))
        D[d_inx]['E'] = int(float(East[i]))
        d_inx += 1

    Connectivity = {}
    Connectivity['connection'] = []
    Connectivity['weight'] = {}
    for i in range(len(edges)):
        # print(str(edges[i][0]) + "   " + str(edges[i][1]) + "   " + str(weight[i]) + "")
        Connectivity['connection'] += [[edges[i][0],edges[i][1]]]
        Connectivity['weight'][str([edges[i][0],edges[i][1]])] = weight[i]

    return D, Connectivity


def generate_BT_adjacent_matrix():
    #  ================ Generate Devices connection =============
    D = {}

    # depth_idx = np.zeros(n_depth)
    # total_idx = 0

    D, Connectivity = generate_device_list(D)
    # print(D)

    #  ================ Generate adjacent_matrix
    adjacent_matrix = np.zeros((len(D), len(D)))

    for x in range(len(D)):
        print('\rProcessing BT raw data ['+str(int(100*np.round(x/len(D),2)))+'%], generating adjacent matrix...',end='')
        for y in range(len(D)):
            link_l = [x, y]
            link_r = [y, x]
            if link_l in Connectivity['connection'] or link_r in Connectivity['connection']:
                adjacent_matrix[x, y] = 1
    #         if D[x][0] == D[y][0] - 1 and D[x][1] == np.floor(D[y][1] / n_branch):
    #             adjacent_matrix[x, y] = 1
    #         if D[x][0] == D[y][0] + 1 and D[y][1] == np.floor(D[x][1] / n_branch):
    #             adjacent_matrix[x, y] = 1
    print(' Done')
    return D, adjacent_matrix


def device_list_to_path(G, adjacent_matrix, in_device_list, out_device_list, DINC_config):
    number_devices = np.shape(adjacent_matrix)[0]
    P = {}
    path_idx = 0
    for i in in_device_list:
        for o in out_device_list:

            if i == o:
                continue
            for path in nx.all_simple_paths(G, source=i, target=o,cutoff=DINC_config['network config']['ttl']):
            # for path in nx.all_shortest_paths(G, source=i, target=o):
                P[path_idx] = path
                path_idx += 1
                # print(path)
            # P, path_idx, _ = device_list_to_path_solver(P, adjacent_matrix, i, o, path_idx, [i], number_devices, True)
    return P


def generate_network_topology(manually_config=True):
    DINC_config = reload_DINC_config('src/configs/DINC_config.json')
    # # =================== set DINC network branch in config ===================
    # question = 'Where is the branch number on each node of your network?'
    # default = 2
    # DINC_config = take_CLI_input(DINC_config, 'network config', 'n_branch', question, default, manually_config,
    #                              numeric=True)

    # n_depth = DINC_config['network config']['n_depth']
    # n_branch = DINC_config['network config']['n_branch']
    Network_Topology = {}

    Network_Topology['device_list'], Network_Topology['adjacent_matrix'] = generate_BT_adjacent_matrix()

    adjacent_matrix = Network_Topology['adjacent_matrix']

    # from adjacent matrix to graph
    Network_Graph = nx.DiGraph()
    for i in range(np.shape(adjacent_matrix)[0]):
        for j in range(np.shape(adjacent_matrix)[1]):
            if adjacent_matrix[i][j] == 1:
                Network_Graph.add_edge(i, j)
    Network_Topology['Graph'] = Network_Graph
    fig, ax = plt.subplots(figsize=(50, 30))
    nx.draw(Network_Graph, with_labels=False, node_size=10, node_color="skyblue", node_shape="o", alpha=0.8,
            linewidths=1)
    DINC_config['directory config']['log plot file name'] = DINC_config['network config']['topology'] + '.pdf'
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

    # =================== set network TTL in config ===================
    question = 'Where is the TTL setting of your network?'
    default = 5
    DINC_config = take_CLI_input(DINC_config, 'network config', 'ttl', question, default, manually_config,
                                 numeric=True)
    P = device_list_to_path(Network_Graph, adjacent_matrix, in_device_list, out_device_list, DINC_config)
    Network_Topology['Path'] = copy.deepcopy(P)

    #  test used to remove graph ====================================
    No_Graph_Network_Topology = {}
    for keys in Network_Topology.keys():
        if keys == 'Graph':
            continue
        No_Graph_Network_Topology[keys] = copy.deepcopy(Network_Topology[keys])
    dump_DINC_config(No_Graph_Network_Topology, 'src/configs/Network_Topology.json')
    #  test used to remove graph ====================================

    default_architectures = []
    default_use_cases = []
    default_targets = []
    for d in Network_Topology['device_list']:
        default_architectures += ['v1model']
        default_use_cases += ['standard_block']
        default_targets += ['bmv2']

    question = 'What architectures would you like to use?'
    DINC_config = take_CLI_input(DINC_config, 'network config', 'architectures', question, default_architectures,
                                 manually_config)

    question = 'What use cases would you like to use?'
    DINC_config = take_CLI_input(DINC_config, 'network config', 'use cases', question, default_use_cases,
                                 manually_config)

    question = 'What targets would you like to use?'
    DINC_config = take_CLI_input(DINC_config, 'network config', 'targets', question, default_targets, manually_config)

    # dump the config file
    dump_DINC_config(DINC_config, 'src/configs/DINC_config.json')

    return Network_Topology