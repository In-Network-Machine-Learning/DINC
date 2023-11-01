# This file is part of the Planter extend project: DINC.
# This program is a free software tool, which does ensemble in-network machine learning.
# licensed under Apache-2.0
#
# Copyright (c) 2020-2021 Changgang Zheng
# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford & Yale University
# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),
# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)

import copy
import time
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from scipy.optimize import milp
from scipy.optimize import LinearConstraint
from src.functions.config_modification import *
from src.functions.input_CLI import *
#  ================ device, element change to position in x array ================
def write_x_weight_array(array, value, device, element, X, D, E, option='write'):
    position = device * len(E) + element
    if X[position] != 'e:' + str(element) + '→ d:' + str(device):
        print('Warning! Position error in middle_ineq_dict!')
    if option == 'write':
        array[position] = value
    elif option == 'add':
        array[position] += value
    return array



def do_optimization(Network_Topology, P4_Information, manually_config = True):
    DINC_config = reload_DINC_config('src/configs/DINC_config.json')

    D = Network_Topology['device_list']
    adjacent_matrix = Network_Topology['adjacent_matrix']
    G =  Network_Topology['Graph']
    in_device_list = Network_Topology['input device list']
    out_device_list = Network_Topology['output device list']
    P = Network_Topology['Path']
    E = P4_Information['element list']
    E_dependency = P4_Information['element dependency']
    Constrains = {}
    Constrains['elements'] = {}
    Constrains['devices'] = {}
    for resource in DINC_config['network config']['resources list']:
        Constrains['elements'][resource] = P4_Information[resource]
        Constrains['devices'][resource] = Network_Topology[resource]

    X = {}
    idx = 0
    for d in range(len(D)):
        for e in range(len(E)):
            X[idx] = 'e:' + str(e) + '→ d:' + str(d)
            idx += 1

    #  ================ following codes are making sure each component follow dependency ================
    middle_idx = 0
    middle_ineq_dict = {}
    for e_idx in E_dependency:
        for path_idx in P:
            Pi = P[path_idx]
            for pi2 in range(len(Pi)):
                middle_arrray = np.zeros(len(X))
                middle_arrray = write_x_weight_array(middle_arrray, 1, Pi[pi2], E_dependency[e_idx][1], X, D, E)
                for pi1 in range(pi2 + 1):
                    middle_arrray = write_x_weight_array(middle_arrray, -1, Pi[pi1], E_dependency[e_idx][0], X, D, E)
                middle_ineq_dict[middle_idx] = {}
                middle_ineq_dict[middle_idx]['middle'] = copy.deepcopy(middle_arrray)
                middle_ineq_dict[middle_idx]['right'] = 0
                middle_ineq_dict[middle_idx]['left'] = -np.inf
                middle_idx += 1
    #  ================ following codes are making sure at least appear once ================
    for e in E:
        for path_idx in P:
            Pi = P[path_idx]
            middle_arrray = np.zeros(len(X))
            for d in (Pi):
                middle_arrray = write_x_weight_array(middle_arrray, -1, d, e, X, D, E)
            middle_ineq_dict[middle_idx] = {}
            middle_ineq_dict[middle_idx]['middle'] = copy.deepcopy(middle_arrray)
            middle_ineq_dict[middle_idx]['right'] = -1
            middle_ineq_dict[middle_idx]['left'] = -np.inf
            middle_idx += 1

    #  ================ following codes are constrains ================
    for resource in DINC_config['network config']['resources list']:

        R_devices = Constrains['devices'][resource]
        R_elements =  Constrains['elements'][resource]

        used_D = []
        for p_idx in P:
            Pi = P[p_idx]
            for d in Pi:
                if d not in used_D:
                    used_D += [d]

        for d in used_D:
            middle_arrray = np.zeros(len(X))
            for e in E:
                middle_arrray = write_x_weight_array(middle_arrray, R_elements[e], d, e, X, D, E, option='add')
            middle_ineq_dict[middle_idx] = {}
            middle_ineq_dict[middle_idx]['middle'] = copy.deepcopy(middle_arrray)
            middle_ineq_dict[middle_idx]['right'] = R_devices[d]
            middle_ineq_dict[middle_idx]['left'] = -np.inf
            # print(middle_ineq_dict[middle_idx])
            middle_idx += 1

    # #  ================ following codes are making sure applied to memory constrains ================
    # Md = np.ones(len(D)) * 12
    #
    # Me = np.ones(len(D)) * 3
    #
    # used_D = []
    # for p_idx in P:
    #     Pi = P[p_idx]
    #     for d in Pi:
    #         if d not in used_D:
    #             used_D += [d]
    #
    # for d in used_D:
    #     middle_arrray = np.zeros(len(X))
    #     for e in E:
    #         middle_arrray = write_x_weight_array(middle_arrray, Me[d], d, e, X, D, E, option='add')
    #     middle_ineq_dict[middle_idx] = {}
    #     middle_ineq_dict[middle_idx]['middle'] = copy.deepcopy(middle_arrray)
    #     middle_ineq_dict[middle_idx]['right'] = Md[d]
    #     middle_ineq_dict[middle_idx]['left'] = -np.inf
    #     # print(middle_ineq_dict[middle_idx])
    #     middle_idx += 1
    #
    # #  ================ following codes are making sure applied to Stage constrains ================
    # Sd = np.ones(len(D)) * 12
    # Sd[1] -= 3
    # Se = np.ones(len(D)) * 5
    #
    # used_D = []
    # for p_idx in P:
    #     Pi = P[p_idx]
    #     for d in Pi:
    #         if d not in used_D:
    #             used_D += [d]
    #
    # for d in used_D:
    #     middle_arrray = np.zeros(len(X))
    #     for e in E:
    #         middle_arrray = write_x_weight_array(middle_arrray, Se[d], d, e, X, D, E, option='add')
    #     middle_ineq_dict[middle_idx] = {}
    #     middle_ineq_dict[middle_idx]['middle'] = copy.deepcopy(middle_arrray)
    #     middle_ineq_dict[middle_idx]['right'] = Sd[d]
    #     middle_ineq_dict[middle_idx]['left'] = -np.inf
    #     # print(middle_ineq_dict[middle_idx])
    #     middle_idx += 1
    #
    # #  ================ following codes are making sure applied to Parser state constrains ================
    # PSd = np.ones(len(D)) * 12
    #
    # PSe = np.ones(len(D)) * 3
    #
    # used_D = []
    # for p_idx in P:
    #     Pi = P[p_idx]
    #     for d in Pi:
    #         if d not in used_D:
    #             used_D += [d]
    #
    # for d in used_D:
    #     middle_arrray = np.zeros(len(X))
    #     for e in E:
    #         middle_arrray = write_x_weight_array(middle_arrray, PSe[d], d, e, X, D, E, option='add')
    #     middle_ineq_dict[middle_idx] = {}
    #     middle_ineq_dict[middle_idx]['middle'] = copy.deepcopy(middle_arrray)
    #     middle_ineq_dict[middle_idx]['right'] = PSd[d]
    #     middle_ineq_dict[middle_idx]['left'] = -np.inf
    #     # print(middle_ineq_dict[middle_idx])
    #     middle_idx += 1

    #  ================ following codes are making sure minimal memory ================
    obj = np.zeros(len(X))
    Mem = np.ones(len(X))
    Mem[0] += 1

    coef_obj_mem = 1
    # *coef_obj_partition

    for xi in range(len(X)):
        obj[xi] += coef_obj_mem * Mem[xi]

    #  ================ following codes are making sure minimal partitions ================
    coef_obj_partition = 1
    # *coef_obj_partition

    for i in range(len(X)):
        obj[i] += coef_obj_partition * 1

    #  ================ following codes are making sure minimal latency ================
    coef_obj_latency = 3
    e = len(E) - 1
    for path_idx in P:
        Pi = P[path_idx]
        for p in range(len(Pi)):
            d = Pi[p]
            obj = write_x_weight_array(obj, coef_obj_latency * p, d, e, X, D, E, option='add')

    # print(obj)

    #     print(dict)
    # print('===================')
    # ================ following codes are making sure it is 0-1 programming ================

    for x_idx in range(len(X)):
        middle_arrray = np.zeros(len(X))
        middle_arrray[x_idx] = 1
        middle_ineq_dict[middle_idx] = {}
        middle_ineq_dict[middle_idx]['middle'] = copy.deepcopy(middle_arrray)
        middle_ineq_dict[middle_idx]['right'] = 1
        middle_ineq_dict[middle_idx]['left'] = 0
        middle_idx += 1

    # x_idx = 0
    # for dict in range(len(middle_ineq_dict), len(middle_ineq_dict)+len(X)):
    #     # print(dict)
    #     middle_ineq[dict, x_idx] = 1
    #     rhs_ineq[dict] = 1
    #     x_idx+=1
    #
    # lhs_ineq = np.full_like(rhs_ineq, -np.inf)
    # for dict in range(len(middle_ineq_dict), len(middle_ineq_dict)+len(X)):
    #     lhs_ineq[dict] = 0
    #

    #  ===================
    middle_ineq = np.zeros((len(middle_ineq_dict), len(X)))
    rhs_ineq = np.zeros(len(middle_ineq_dict))
    lhs_ineq = np.zeros(len(middle_ineq_dict))

    for dict in middle_ineq_dict:
        middle_ineq[dict, :] = middle_ineq_dict[dict]['middle']
        rhs_ineq[dict] = middle_ineq_dict[dict]['right']
        lhs_ineq[dict] = middle_ineq_dict[dict]['left']

    # =========== do optimization
    # https://scipy.github.io/devdocs/reference/generated/scipy.optimize.milp.html
    constraints = LinearConstraint(middle_ineq, lhs_ineq, rhs_ineq)
    integrality = np.ones_like(obj)
    res = milp(c=obj, constraints=constraints, integrality=integrality)
    res.x
    if 'successful' not in res.message:
        print(res.message)
        print('Exit... The programmable network does not have enough resource.')
        exit()
    print(res)

    node_codition = {}
    node_codition_raw_for_test = {}
    for d in range(len(D)):
        node_codition[d] = ' '
        node_codition_raw_for_test[d] = []

    for e in E:
        E[e]['duplication'] = 0
    for x_idx in range(len(res.x)):
        # print(x_idx, res.x[x_idx], node_codition[np.floor(x_idx / len(E))])
        if int(np.round(res.x[x_idx], 1)) == 1:
            if node_codition[np.floor(x_idx / len(E))] == ' ':
                node_codition[np.floor(x_idx / len(E))] = 'E' + str(x_idx % len(E))
            else:
                node_codition[np.floor(x_idx / len(E))] += ' E' + str(x_idx % len(E))
            node_codition_raw_for_test[np.floor(x_idx / len(E))] += [x_idx % len(E)]
            E[int(x_idx % len(E))]['duplication'] += 1
    for e in E:
        print('Element ', e, ' has ', E[e]['duplication'], ' duplications.')

    # print(res.x,  len(E), node_codition)
    node_labels = {}
    used_nodes = 0
    for node in G.nodes:
        node_labels[node] = 'D' + str(node) + '<=' + node_codition[node]
        if 'E' in node_codition[node]:
            used_nodes += 1
    pos = nx.spring_layout(G)
    # nx.draw_networkx_labels(G, pos, labels=node_labels)
    nx.draw(G, labels=node_labels, node_size=500, node_color="skyblue", node_shape="o", alpha=0.5, linewidths=5,
            font_size=8)
    log_dir = './src/logs/'+ DINC_config['directory config']['p4 file'].split('/')[-1][:-3] + '_' + DINC_config['directory config']['log plot file name']
    plt.savefig(log_dir, dpi=600, format='pdf', bbox_inches='tight')
    print('Optimization finished, the result can be found in the directory:', log_dir)
    # plt.show()
    # =================== test the ILP solver? ===================
    question = 'If you want to test the ILP solver?'
    default = False
    DINC_config = take_CLI_input(DINC_config, 'operation config', 'test ILP', question, default, manually_config)
    if DINC_config['operation config']['test ILP'] != False:
        question = 'If you want detailed test info?'
        default = False
        DINC_config = take_CLI_input(DINC_config, 'operation config', 'test details', question, default,
                                     manually_config)
        print('The used number of nodes is', used_nodes, 'out of', int(len(D.keys())))
        time_list = []
        for t in range(10):
            start = time.time()
            _ = milp(c=obj, constraints=constraints, integrality=integrality)
            end = time.time()
            time_list += [end - start]
            if DINC_config['operation config']['test details'] == False:
                print("\rExecution time for round", t+1, "test is: %fs" % (end - start),end="")
            else:
                print("Execution time for round", t + 1, "test is: %fs" % (end - start))

        if DINC_config['operation config']['test details'] == False:
            print('\nEverage execution time is '+ str(np.average(time_list))+ 's with standard deviation '+str(np.std(time_list))+'s')
        else:
            print('Everage execution time is '+ str(np.average(time_list))+ 's with standard deviation '+str(np.std(time_list))+'s')
        total_path_len = 0
        hops_num_list = []
        total_hop_num = 0
        count = 0
        for p_idx in P:
            path_len = len(P[p_idx])
            hops_num = 1
            E_along_path = []
            for d in P[p_idx]:
                for e in node_codition_raw_for_test[d]:
                    if e not in E_along_path:
                        E_along_path += [e]
                if len(E.keys()) == len(E_along_path):
                    # print('Path ' + str(p_idx) + '/' + str(len(P.keys())) + ' latency is', hops_num, 'out of', path_len, 'hops' )
                    if DINC_config['operation config']['test details'] == False:
                        print('\rPath ' + str(p_idx + 1) + '/' + str(len(P.keys())) + ' latency is', hops_num, 'out of',
                              path_len, 'hops', end='')
                    else:
                        print('Path ' + str(p_idx + 1) + '/' + str(len(P.keys())) + ' latency is', hops_num, 'out of',
                              path_len, 'hops')
                    total_hop_num += hops_num
                    total_path_len += path_len
                    hops_num_list += [hops_num]
                    count += 1
                    break
                hops_num += 1
        if DINC_config['operation config']['test details'] == False:
            print('\nDINC deployment has', count, 'paths with average latency:', total_hop_num / count, 'out of',
                  total_path_len / count, 'hops')
        else:
            print('DINC deployment has',count,'paths with average latency:', total_hop_num/count, 'out of', total_path_len/count, 'hops')


        max_hops = 0
        for p_idx in P:
            if len(P[p_idx])>max_hops:
                max_hops = len(P[p_idx])
        hops_cdf = np.zeros(max_hops)
        accumulate_paths = 0
        for h_num in range(max_hops):
            accumulate_paths += hops_num_list.count(h_num+1)
            hops_cdf[h_num] = accumulate_paths/len(P.keys())
        print('The hop number CDF is:', hops_cdf)
        print('Orignial segmentation number is '+str(len(E.keys()))+ ', total used segmentation is '+str(int(np.sum(res.x))))

    # dump the config file
    dump_DINC_config(DINC_config, 'src/configs/DINC_config.json')
    return node_codition




