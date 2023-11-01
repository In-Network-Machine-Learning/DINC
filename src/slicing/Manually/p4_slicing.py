import re

import numpy as np

from src.functions.input_CLI import *
from src.functions.config_modification import *
from src.functions.add_license import *
from src.functions.write_file import *
import copy
def read_marker_info_from_str(line_str_input, starter = '-=<', ender = '>=-'):
    start_marker_obj = re.finditer(starter, line_str_input)
    end_marker_obj = re.finditer(ender, line_str_input)
    start_marker = []
    end_marker = []
    results = []
    for m in start_marker_obj:
        start_marker += [m.span()[1]]
    for e in end_marker_obj:
        end_marker += [e.span()[0]]
    for i in range(len(start_marker)):
        s = start_marker[i]
        e = end_marker[i]
        out_str = line_str_input[s:e].split(',')
        for i in range(len(out_str)):
            out_str[i] = out_str[i].lstrip().rstrip()
        results += [out_str]
    return results



def retrieve_p4_information(manually_config = True):
    DINC_config = reload_DINC_config('src/configs/DINC_config.json')
    p4_file_name = DINC_config['directory config']['p4 file']

    # ========= Check the start marker =========
    question = 'Where is the stater marker in your P4 code?'
    default = '@!'
    DINC_config = take_CLI_input(DINC_config, 'p4 config', 'start marker', question, default, manually_config, numeric=False)

    # ========= Check the end marker =========
    question = 'Where is the end marker in your P4 code?'
    default = '!@'
    DINC_config = take_CLI_input(DINC_config, 'p4 config', 'end marker', question, default, manually_config, numeric=False)

    P4_Configuration = {}

    # ========= Check the end marker =========
    question = 'What is the element position information marked in your P4 code?'
    default = '[slice, position]'
    DINC_config = take_CLI_input(DINC_config, 'p4 config', 'key element info', question, default, manually_config, numeric=False)
    DINC_config['p4 config']['key element info'] = str_to_array(DINC_config['p4 config']['key element info'], margine= 1)
    # Label current part
    slice_position = DINC_config['p4 config']['key element info']
    Current = {}

    # record all the created sliced p4 file
    DINC_config['p4 config']['existed sliced p4 file'] = []

    clean_dir(DINC_config['directory config']['work'] + '/src/temp/P4')

    # Label the current slice and its position
    with open(p4_file_name, 'r') as file:
        e = 'not_slice_marker'
        for line_idx, line in enumerate(file.readlines()):
            #  if marker appears
            if DINC_config['p4 config']['start marker'] in line:
                results = read_marker_info_from_str(line, DINC_config['p4 config']['start marker'], DINC_config['p4 config']['end marker'])

                for r_idx, r in enumerate(results):
                    #  if it is a new start of marker field
                    if 'slice' in r:
                        e = results[r_idx][1]
                    #  if it is a new end of marker field
                    if 'end' in r and r[1] == e:
                        e = 'not_slice_marker'
                    for s_p in slice_position:
                        if s_p in r:
                            Current[s_p] = r[1]
                Current['file_name'] = DINC_config['directory config']['work'] + '/src/temp/P4/E'
                for i, s_p in enumerate(slice_position):
                    if i == 0:
                        Current['file_name'] += Current[s_p]
                    else:
                        Current['file_name'] += '_' + Current[s_p]
                Current['file_name'] +='.p4'

                #  if is inside a marker field
                if e != 'not_slice_marker':
                    #  inclide all marker information to the P4_Configuration
                    if e not in P4_Configuration:
                        P4_Configuration[e] = {}
                    for r_idx, r in enumerate(results):
                        if r[0] not in P4_Configuration[e]:
                            P4_Configuration[e][r[0]] = [r[1:]]
                        elif r[1:] not in P4_Configuration[e][r[0]]:
                            P4_Configuration[e][r[0]] += [r[1:]]
            # after starts of marker fields, all lines with out marker will be saved before the end
            elif e != 'not_slice_marker':
                if Current['file_name'] not in DINC_config['p4 config']['existed sliced p4 file']:
                    DINC_config['p4 config']['existed sliced p4 file'] += [Current['file_name']]
                    write_line(line, Current['file_name'], first_line_of_file=True)
                else:
                    write_line(line, Current['file_name'], first_line_of_file=False)

    P4_Information = {}
    P4_Information['element list'] = {}
    P4_Information['element dependency'] = {}
    E_dependency = []

    for s in P4_Configuration.keys():
        P4_Information['element list'][int(s)] = {}
        # print(P4_Information)
        # print(P4_Configuration)
        # print(P4_Configuration[s])
        for p_list in P4_Configuration[s]['previous']:
            for p in p_list:
                if p.isdigit():
                    dependency = [int(p), int(s)]
                    if dependency not in E_dependency:
                        E_dependency += [dependency]

    for i,d in enumerate(E_dependency):
        P4_Information['element dependency'][i] = d



    for i in P4_Information['element list'].keys():
        P4_Information['element list'][i]['metadata_in'] = P4_Configuration[str(i)]['metadata_in']
        P4_Information['element list'][i]['metadata_out'] = P4_Configuration[str(i)]['metadata_out']
        P4_Information['element list'][i]['stage'] = int(P4_Configuration[str(i)]['stage'][0][0])
        P4_Information['element list'][i]['memory'] = int(P4_Configuration[str(i)]['memory'][0][0])

    for resource in DINC_config['network config']['resources list']:
        element_resource_list = np.zeros(len(P4_Information['element list']))
        for i in P4_Information['element list'].keys():
            if resource in P4_Information['element list'][i].keys():
                element_resource_list[i] = P4_Information['element list'][i][resource]
        DINC_config['p4 config'][resource] = copy.deepcopy(element_resource_list.astype(int).tolist())
        P4_Information[resource] = DINC_config['p4 config'][resource]

    for e in P4_Information['element list'].keys():
        P4_Information['element list'][e]['dependent'] = []
        for p_e_list in P4_Configuration[str(e)]['previous']:
            for p_e in p_e_list:
                if p_e.isdigit():
                    if int(p_e) not in P4_Information['element list'][e]['dependent']:
                        P4_Information['element list'][e]['dependent'] += [int(p_e)]
    # dump the config file
    dump_DINC_config(DINC_config, 'src/configs/DINC_config.json')

    return P4_Information



if __name__ == "__main__":
    print(read_marker_info_from_str('  // dependency marker @!slice, 1, 2,4!@@!   4!@ @!previous, none!@ @!position, apply!@', '@!', '!@'))