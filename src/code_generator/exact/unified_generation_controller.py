# This file is part of the Planter extend project: DINC.
# This program is a free software tool, which does ensemble in-network machine learning.
# licensed under Apache-2.0
#
# Copyright (c) 2020-2021 Changgang Zheng
# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford & Yale University
# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),
# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)
import copy
import sys
import os
import json
import shutil
import numpy as np
from src.functions.config_modification import *
from src.functions.write_file import *
import networkx as nx

###################################################
# Load the configuration from the config file
# input: Allocation, P4_information['element list']
# output: Storage Allocation
###################################################

# def tight_storage_allocation(Allocation, P4_Information):
#     Storage = {}
#     for d in Allocation:
#         Storage[d] = {}
#         Storage[d]['read'] = {}
#         Storage[d]['write'] = {}
#     # Warning ============ Function not finished ============
#     return Storage

def metadata_supplement(p, D_to_rE, P4_Information, p_idx , D_to_M = {}, P_to_Option = [], E_list = []):
    if p_idx < 0:
        all_used_E = sorted([j for i in E_list for j in i])
        all_E = sorted(P4_Information['element list'].keys())
        if all_used_E == all_E:
            count = 0
            for idx, d in enumerate(reversed(p)):
                P_to_O_idx = len(p) - idx -1
                if D_to_rE[d][P_to_Option[P_to_O_idx]]:
                    if count == 0:
                        meta_bottom_up = copy.deepcopy(D_to_M[d][P_to_Option[P_to_O_idx]]['input'])
                        # print(d, 'b init ------- meta_bottom_up', meta_bottom_up)
                    else:
                        for m in copy.deepcopy(meta_bottom_up):
                            if m in D_to_M[d][P_to_Option[P_to_O_idx]]['output']:
                                meta_bottom_up.remove(m)
                        # print(d, 'd------- meta_bottom_up', meta_bottom_up)
                        for m in meta_bottom_up:
                            if m not in D_to_M[d][P_to_Option[P_to_O_idx]]['output']:
                                D_to_M[d][P_to_Option[P_to_O_idx]]['output'] += [m]
                        # D_to_M[d][P_to_Option[P_to_O_idx]]['output'] += meta_bottom_up
                        input_missing_meta = []
                        # print(1)
                        for m in meta_bottom_up:
                            if m not in D_to_M[d][P_to_Option[P_to_O_idx]]['input']:
                                input_missing_meta += [m]
                        meta_bottom_up = copy.deepcopy(input_missing_meta)
                        for m in meta_bottom_up:
                            if m not in D_to_M[d][P_to_Option[P_to_O_idx]]['input']:
                                D_to_M[d][P_to_Option[P_to_O_idx]]['input'] += [m]
                        meta_bottom_up = copy.deepcopy(D_to_M[d][P_to_Option[P_to_O_idx]]['input'])
                    count += 1
        return D_to_M
    for option in D_to_rE[p[p_idx]]:
        P_to_Option += [option]
        # print(D_to_rE[p[p_idx]][option])
        E_list += [D_to_rE[p[p_idx]][option]]
        p_idx -= 1
        D_to_M = metadata_supplement(p, D_to_rE, P4_Information, p_idx, D_to_M, P_to_Option, E_list)
        P_to_Option = P_to_Option[:-1]
        E_list = E_list[:-1]
    return D_to_M

def generator(Allocation, P4_Information, Network_Topology, manually_config = True):
    DINC_config = reload_DINC_config('src/configs/DINC_config.json')
    if DINC_config['p4 config']['begin test'] == "T":
        pass
    else:
        clean_dir(DINC_config['directory config']['work'] + '/P4')
    # clean_dir(DINC_config['directory config']['work'] + '/P4')
    # total_bits = 0
    D_to_E = {} # The funtion required (E) on each device (D)
    for d in Allocation:
        D_to_E[d] = []
        # used_bits = 0
        for e in list(P4_Information['element list'].keys()):
            if 'E'+str(e) in Allocation[d]:
                D_to_E[d] += [e]
                for m in P4_Information['element list'][e]['metadata_in']:
                    start = m[0].index('<')+1
                    end = m[0].index('>')
                    # used_bits += int(m[0][start:end])
                    if len(m) == 2:
                        m += [int(m[0][start:end])]
        # if used_bits> total_bits:
        #     total_bits = used_bits

        # used_bits = 0
        for e in list(P4_Information['element list'].keys()):
            if 'E' + str(e) in Allocation[d]:
                # D_to_E[d] += [e]
                for m in P4_Information['element list'][e]['metadata_out']:
                    start = m[0].index('<') + 1
                    end = m[0].index('>')
                    # used_bits += int(m[0][start:end])
                    if len(m) == 2:
                        m += [int(m[0][start:end])]
        # if used_bits > total_bits:
        #     total_bits = used_bits

    D_to_p1E = {} # The possible (p)revious node functionality (E) on each device (D)
    for d in Allocation:
        D_to_p1E[d] = {}
    for d_in in Network_Topology['input device list']:
        for d_out in Network_Topology['output device list']:
            path_list = nx.all_simple_paths(Network_Topology['Graph'], source=d_in, target=d_out)
            for p in path_list:
                previous = []
                for idx, d in enumerate(p):
                    if previous and previous not in D_to_p1E[d].values():
                        D_to_p1E[d][len(D_to_p1E[d].keys())] = previous
                    previous = D_to_E[d]

    D_to_pE = {}  # The possible (p)revious node functionality (E) on each device (D)
    for d in Allocation:
        D_to_pE[d] = {}
    for d_in in Network_Topology['input device list']:
        for d_out in Network_Topology['output device list']:
            path_list = nx.all_simple_paths(Network_Topology['Graph'], source=d_in, target=d_out)
            for p in path_list:
                # previous = []
                path = []
                for idx, d in enumerate(p):
                    if list(set(path)) not in D_to_pE[d].values():
                        D_to_pE[d][len(D_to_pE[d].keys())] = copy.deepcopy(list(set(path)))
                    path += D_to_E[d]

    D_to_rE = {} # The (r)eal node functionality (E) partition on each device (D)
    for d in Allocation:
        D_to_rE[d] = {}
        for option_idx in D_to_pE[d].keys():
            E_list = []
            for cE in D_to_E[d]:
                if cE not in D_to_pE[d][option_idx]:
                    E_list += [cE]
            if list(set(E_list)) not in D_to_rE[d].values():
                D_to_rE[d][len(D_to_rE[d].keys())] = copy.deepcopy(E_list)


    E_to_M = {}
    for e in P4_Information['element list']:
        E_to_M[e] = {}
        E_to_M[e]['input'] = []
        E_to_M[e]['output'] = []
        for m in P4_Information['element list'][e]['metadata_in']:
            E_to_M[e]['input'] += m
        for m in P4_Information['element list'][e]['metadata_out']:
            E_to_M[e]['output'] += m



    D_to_M = {}
    for d in Allocation:
        D_to_M[d] = {}
        for idx in D_to_rE[d]:
            D_to_M[d][idx] = {}
            D_to_M[d][idx]['input'] = []
            D_to_M[d][idx]['output'] = []

            E_out_D_drop = []
            E_in_D_drop = []
            for e in D_to_rE[d][idx]:
                for e_dependent in P4_Information['element list'][e]['dependent']:
                    if e_dependent in D_to_rE[d][idx]:
                        if int(e_dependent) not in E_out_D_drop:
                            E_out_D_drop += [int(copy.deepcopy(e_dependent))]
                        if int(e) not in E_in_D_drop:
                            E_in_D_drop += [int(copy.deepcopy(e))]

            for e in D_to_rE[d][idx]:
                if e not in E_in_D_drop:
                    D_to_M[d][idx]['input'] += P4_Information['element list'][e]['metadata_in']
                if e not in E_out_D_drop:
                    D_to_M[d][idx]['output'] += P4_Information['element list'][e]['metadata_out']

            input_M = []
            output_M = []
            for e in D_to_rE[d][idx]:
                input_M += P4_Information['element list'][e]['metadata_in']
                output_M += P4_Information['element list'][e]['metadata_out']
            if d == 1:
                print('before remove input m', input_M, 'output m', output_M)
            for meta in copy.deepcopy(input_M):
                if meta in copy.deepcopy(output_M):
                    input_M.remove(meta)
                    output_M.remove(meta)
            if d == 1:
                print('input m', input_M, 'output m', output_M)
            for meta in input_M:
                if meta not in D_to_M[d][idx]['input']:
                    D_to_M[d][idx]['input'] += copy.deepcopy([meta])
            for meta in output_M:
                if meta not in D_to_M[d][idx]['output']:
                    D_to_M[d][idx]['output'] += copy.deepcopy([meta])


    D_to_M = copy.deepcopy(D_to_M)
    for p_idx in Network_Topology['Path']:
        p = Network_Topology['Path'][p_idx]
        D_to_M = metadata_supplement(p, D_to_rE, P4_Information, len(p)-1, D_to_M, P_to_Option = [], E_list = [])

    for d in Allocation:
        for idx in D_to_M[d]:
            D_to_M[d][idx]['input'] = sorted(D_to_M[d][idx]['input'])
            D_to_M[d][idx]['output'] = sorted(D_to_M[d][idx]['output'])

    D_to_allM = {}
    for d in Allocation:
        D_to_allM[d] = {}
        m_list = []
        m_in_list = []
        m_out_list = []

        for inx in D_to_M[d]:
            for m in D_to_M[d][idx]['input']:
                if m not in m_list:
                    m_list += [m]
                if m not in m_in_list:
                    m_in_list += [m]
            for m in D_to_M[d][idx]['output']:
                if m not in m_list:
                    m_list += [m]
                if m not in m_out_list:
                    m_out_list += [m]
            for e in D_to_E[d]:
                for rm in P4_Information['element list'][e]['metadata_in']:
                    if rm not in m_list:
                        m_list += [rm]
                for rm in P4_Information['element list'][e]['metadata_out']:
                    if rm not in m_list:
                        m_list += [rm]
        D_to_allM[d]['all'] = copy.deepcopy(sorted(m_list))
        D_to_allM[d]['input'] = copy.deepcopy(sorted(m_in_list))
        D_to_allM[d]['output'] = copy.deepcopy(sorted(m_out_list))


    total_bits = 0
    for d in Allocation:
        for idx in D_to_M[d]:
            used_bits = 0
            for e in list(D_to_M[d][idx]['input']):
                used_bits += e[2]
            if used_bits> total_bits:
                total_bits = used_bits
            used_bits = 0
            for e in list(D_to_M[d][idx]['output']):
                used_bits += e[2]
            if used_bits > total_bits:
                total_bits = used_bits

    D_P4_Info = {}
    for d in Allocation:
        D_P4_Info[d] = {}
        D_P4_Info[d]['D_to_p1E'] = D_to_p1E[d]
        D_P4_Info[d]['D_to_pE'] = D_to_pE[d]
        D_P4_Info[d]['D_to_rE'] = D_to_rE[d]
        D_P4_Info[d]['D_to_E'] = D_to_E[d]
        D_P4_Info[d]['D_to_M'] = D_to_M[d]
        D_P4_Info[d]['D_to_allM'] = D_to_allM[d]

    config = {}
    config['storage bits'] = 32
    config['number storage'] = int(np.ceil(total_bits/config['storage bits']))
    config['element dependency'] = P4_Information['element dependency']
    # config['element metadata'] = E_to_M
    # config['device to element'] = D_to_E
    config['D_P4_Info'] = D_P4_Info
    config['DINC work'] = DINC_config['directory config']['work']
    # config['Storage'] = tight_storage_allocation(Allocation, P4_Information)
    for node_idx in Allocation.keys():
        # print('pre:', node_idx, config['D_P4_Info'][node_idx]['D_to_rE'])
        # if 'E' not in Allocation[node_idx]:
        #     continue
        use_case = DINC_config['network config']['use cases'][node_idx]
        architecture = DINC_config['network config']['architectures'][node_idx]
        use_case_path = DINC_config['directory config']['work'] + '/src/use_cases/' + use_case
        print('+ Add the following path: ' + use_case_path)
        sys.path.append(use_case_path)
        architecture_path = DINC_config['directory config']['work'] + '/src/architecture/' + architecture
        print('+ Add the following path: ' + architecture_path)
        sys.path.append(architecture_path)

        from p4_generator import generate_p4
        config['node index'] = node_idx
        file_name = 'Node_' + str(node_idx) + '.p4'
        p4_file = DINC_config['directory config']['work'] + '/P4/' + file_name
        print('> Generating p4 files with ' + architecture + ' and ' + use_case + ' for node ' + str(node_idx) + ' -> ' + file_name + '...', end="")
        generate_p4(Allocation, DINC_config, config, p4_file)

        print('- Remove the following path: ' + use_case_path)
        sys.path.remove(use_case_path)
        print('- Remove the following path: ' + architecture_path)
        sys.path.remove(architecture_path)
    print("P4 Generation Finished!")