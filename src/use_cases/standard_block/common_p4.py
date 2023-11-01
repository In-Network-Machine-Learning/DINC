# This file is part of the Planter extend project: DINC.
# This program is a free software tool, which does ensemble in-network machine learning.
# licensed under Apache-2.0
#
# Copyright (c) 2020-2021 Changgang Zheng
# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford & Yale University
# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),
# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)
import copy
import os.path
import numpy as np
from src.functions.write_file import *

def common_constants(fname, config):
    with open(fname, 'a') as headers:
        headers.write("const bit<16> TYPE_IPV4 = 0x800;\n"
                      "const bit<16> TYPE_DINC = 0x1234;\n"
                      "const bit<8>  DINC_P     = 0x50;   // 'P'\n"
                      "const bit<8>  DINC_4     = 0x34;   // '4'\n"
                      "const bit<8>  DINC_VER   = 0x01;   // v0.1\n"
                      "typedef bit<9> egressSpec_t;\n"
                      "typedef bit<48> macAddr_t;\n"
                      "typedef bit<32> ip4Addr_t;\n\n")



def common_metadata(fname, config):
    with open(fname, 'a') as headers:

        for e in config['D_P4_Info'][int(config['node index'])]['D_to_allM']['all']:
            metadata = e[0] + ' ' + e[1]
            headers.write("    "+  metadata + ";\n")





def common_headers(fname, config):
    with open(fname, 'a') as headers:
        # write result header

        headers.write("header ethernet_h {\n"
                      "    macAddr_t dstAddr;\n"
                      "    macAddr_t srcAddr;\n"
                      "    bit<16> etherType;\n"
                      "}\n\n")

        headers.write("header ipv4_h{\n"
                      "    bit < 4 > version;\n"
                      "    bit < 4 > ihl;\n"
                      "    bit < 8 > diffserv;\n"
                      "    bit < 16 > totalLen;\n"
                      "    bit < 16 > identification;\n"
                      "    bit < 3 > flags;\n"
                      "    bit < 13 > fragOffset;\n"
                      "    bit < 8 > ttl;\n"
                      "    bit < 8 > protocol;\n"
                      "    bit < 16 > hdrChecksum;\n"
                      "    ip4Addr_t srcAddr;\n"
                      "    ip4Addr_t dstAddr;\n"
                      "}\n\n")

        headers.write("header DINC_h{\n"
                      "    bit<8> p;\n"
                      "    bit<8> four;\n"
                      "    bit<8> ver;\n"
                      "    bit<8> typ;\n"
                      "    bit<32> E_bitmap;\n"
                      "    }\n\n")

        headers.write("header DINC_meta_h{\n")
        for f in range(0, config['number storage']):
            headers.write("    bit<" + str(config["storage bits"]) + "> storage" + str(f) + ";\n")
        headers.write("}\n\n")

        # write the headers' structure
        headers.write("struct header_t {\n"
                      "    ethernet_h   ethernet;\n"
                      "    ipv4_h       ipv4;\n"
                      "    DINC_h       DINC;\n"
                      "    DINC_meta_h  DINC_meta;\n"
                      "}\n\n")


def common_parser(fname, config):
    with open(fname, 'a') as parser:
        parser.write("    state parse_ethernet {\n"
                     "        pkt.extract(hdr.ethernet);\n" 
                     "        transition select(hdr.ethernet.etherType) {\n" 
                     "            TYPE_DINC         : check_DINC_version;\n" 
                     "            TYPE_IPV4         : parse_ipv4;\n" 
                     "            default           : accept;\n" 
                     "        }\n" 
                     "    }\n\n")


        parser.write("    state parse_ipv4 {\n"
                     "        pkt.extract(hdr.ipv4);\n"
                     "        transition accept;\n"
                     "    }\n\n")


        parser.write("    state check_DINC_version {\n"
                     "        pkt.extract(hdr.ipv4);\n"
                     "        transition select(pkt.lookahead<DINC_h>().E_bitmap) {\n" )
                     # "        (DINC_P, DINC_4, DINC_VER) : parse_DINC;\n"
        if config['D_P4_Info'][int(config['node index'])]['D_to_E']:
            for idx in config['D_P4_Info'][int(config['node index'])]['D_to_pE']:
                bitmap = 32*'0'
                for e in config['D_P4_Info'][int(config['node index'])]['D_to_pE'][idx]:
                    bitmap = bitmap[:e] + '1' + bitmap[e+1:]
                bitmap = '0b' + bitmap
                parser.write("        " + bitmap + ": parse_DINC" + str(idx) +";\n")
        parser.write("        default                    : accept;\n"
                     "        }\n"
                     "    }\n\n" )


        # parser.write("    state parse_DINC {\n"
        #              "        pkt.extract(hdr.DINC);\n")
        # for f in range(0, config['number storage']):
        #     parser.write("        meta.feature" + str(f) + " = hdr.DINC.feature" + str(f) + ";\n")
        # parser.write("        meta.flag = 1 ;\n"
        #              "        transition accept;\n"
        #              "    }\n")
        if config['D_P4_Info'][int(config['node index'])]['D_to_E']:
            for idx in config['D_P4_Info'][int(config['node index'])]['D_to_pE']:
                parser.write("    state parse_DINC" + str(idx) +"{\n"
                             "        pkt.extract(hdr.DINC_meta);\n")

                current_storage = 0
                current_bits = 0
                new_storage = 'False'
                extra = 0
                for m_idx, m in enumerate(config['D_P4_Info'][int(config['node index'])]['D_to_M'][idx]['input']):
                    if current_bits + m[2] >= config['storage bits']:
                        parser.write("        meta." + m[1] + " = hdr.DINC_meta.storage" + str(current_storage) + "[" + str(config['storage bits'] - 1) + ":" + str(current_bits) + "]")
                        # parser.write(m[1] + "[" + str(config['storage bits'] - 1) + ":" + str(current_bits) + "];\n")
                        current_storage += 1
                        extra = m[2] - (config['storage bits'] - current_bits)
                        current_bits = 0
                        if extra > 0:
                            parser.write(" ++ hdr.DINC_meta.storage" + str(current_storage) + "[" + str(current_bits + extra - 1) + ":" + str(current_bits) + "];\n")
                            current_bits += extra
                            extra = 0
                        else:
                            parser.write(";\n")


                    else:
                        parser.write("        meta." + m[1] + " = hdr.DINC_meta.storage" + str(current_storage) + "[" + str(current_bits + m[2] - 1) + ":" + str(current_bits) + "];\n")
                        current_bits += m[2]



                parser.write("        transition accept;\n"
                             "    }\n")

def common_tables(fname, config):
    with open(fname, 'a') as ingress:


        ingress.write("    action drop() {\n"
                      "        mark_to_drop(ig_intr_md);\n"
                      "    }\n\n")

        ingress.write("    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {\n"
                      "            ig_intr_md.egress_spec = port;\n"
                      "            hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;\n"
                      "            hdr.ethernet.dstAddr = dstAddr;\n"
                      "            hdr.ipv4.ttl = hdr.ipv4.ttl - 1;\n"
                      "        }\n\n")

        ingress.write("    table ipv4_lpm {\n"
                      "        key = {\n"
                      "            hdr.ipv4.dstAddr: lpm;\n"
                      "        }\n"
                      "        actions = {\n"
                      "            ipv4_forward;\n"
                      "            drop;\n"
                      "            NoAction;\n"
                      "        }\n"
                      "        size = 1024;\n"
                      "        default_action = drop();\n"
                      "    }\n\n")

        for e in config['D_P4_Info'][int(config['node index'])]['D_to_E']:
            sliced_p4_file_name = config['DINC work']+'/src/temp/P4/E' + str(int(e)) + '_control.p4'
            # print('common_table begin')
            if os.path.exists(sliced_p4_file_name):
                use_case_leading_space = 4
                write_p4_file_with_space(sliced_p4_file_name, use_case_leading_space, 0, ingress)
                ingress.write("\n\n")
            # print('common_table ends')
def common_logics(fname, config):
    with open(fname, 'a') as ingress:

        ingress.write("        if (hdr.ipv4.isValid() && hdr.ipv4.ttl > 0) {\n"
                      "            ipv4_lpm.apply();\n"
                      "        }\n\n")


        # print('inside', config['node index'], config['D_P4_Info'][int(config['node index'])]['D_to_rE'])
        if config['D_P4_Info'][int(config['node index'])]['D_to_E']:
            ingress.write("        if (hdr.DINC.isValid()) {\n")
        for e in config['D_P4_Info'][int(config['node index'])]['D_to_E']:
            sliced_p4_file_name = config['DINC work']+'/src/temp/P4/E' + str(int(e)) + '_control-apply.p4'
            if os.path.exists(sliced_p4_file_name):
                ingress.write("            if (hdr.DINC.E_bitmap[" + str(int(e)) + ":" + str(int(e)) + "] != 1) {\n")
                last_use_case = "            if (hdr.DINC.E_bitmap[" + str(int(e)) + ":" + str(int(e)) + "] != 1) {\n"
                use_case_leading_space = len(last_use_case) - len(last_use_case.lstrip(' '))
                write_p4_file_with_space(sliced_p4_file_name, use_case_leading_space, 4, ingress)
                ingress.write("            }\n")

        if config['D_P4_Info'][int(config['node index'])]['D_to_E']:
            for idx in config['D_P4_Info'][int(config['node index'])]['D_to_pE']:
                bitmap = 32*'0'
                for e in config['D_P4_Info'][int(config['node index'])]['D_to_pE'][idx]:
                    bitmap = bitmap[:e] + '1' + bitmap[e+1:]
                bitmap = '0b' + bitmap
                if idx == 0:
                    ingress.write("            if (hdr.DINC.E_bitmap == " + bitmap + "){\n")
                else:
                    ingress.write("            } else if (hdr.DINC.E_bitmap == " + bitmap + "){\n")

                current_storage = 0
                current_bits = 0
                # new_storage = 'False'
                extra = 0
                assignment_left = "                hdr.DINC_meta.storage" + str(current_storage)
                assignment_right = ''
                for m_idx, m in enumerate(config['D_P4_Info'][int(config['node index'])]['D_to_M'][idx]['output']):
                    if current_bits + m[2] >= config['storage bits']:
                        # if new_storage == 'True':
                        #     assignment_left = "                hdr.DINC_meta.storage" + str(current_storage)
                        #     new_storage = 'False'
                        if m[2] - (config['storage bits'] - current_bits) > 0:
                            assignment_right += "meta." + m[1] + "[" + str(config['storage bits'] - current_bits -1) + ":" + str(0) + "];\n"
                        else:
                            assignment_right += "meta." + m[1] + ";\n"
                        ingress.write( copy.deepcopy(assignment_left + " = " + assignment_right))
                        assignment_right = ''
                        current_storage += 1
                        extra = m[2] - (config['storage bits'] - current_bits )
                        current_bits = 0
                        if extra > 0:
                            assignment_left = "                hdr.DINC_meta.storage" + str(current_storage)
                            if m_idx == len(config['D_P4_Info'][int(config['node index'])]['D_to_M'][idx]['output'])-1: # the last meta
                                assignment_right += "meta." + m[1] + "[" + str(m[2]-1) + ":" + str(m[2]-extra) + "];\n"
                                assignment_left += "[" + str(extra-1) + ":" + str(0) + "]"
                                ingress.write(copy.deepcopy(assignment_left + " = " + assignment_right))
                            else:
                                assignment_right += "meta." + m[1] + "[" + str(m[2]-1) + ":" + str(m[2]-extra) + "] ++ "
                            current_bits += extra
                            extra = 0
                        else:
                            if m_idx == len(config['D_P4_Info'][int(config['node index'])]['D_to_M'][idx]['output']) - 1:  # the last meta
                                pass
                            else:
                                assignment_left = "                hdr.DINC_meta.storage" + str(current_storage)
                            # new_storage = 'True'
                    else:
                        # if new_storage == 'True':
                        #     ingress.write("                hdr.DINC_meta.storage" + str(current_storage) + " = ")
                        #     new_storage = 'False'
                        if m_idx == len(config['D_P4_Info'][int(config['node index'])]['D_to_M'][idx]['output']) - 1:  # the last meta
                            assignment_right += "meta." + m[1] + ";\n"
                            assignment_left += "[" + str(current_bits + m[2] - 1) + ":" + str(0) + "]"
                            ingress.write(copy.deepcopy(assignment_left + " = " + assignment_right))
                        else:
                            assignment_right += "meta." + m[1] + " ++ "
                        current_bits += m[2]
                        # print('d', config['node index'], 'current', current_bits)
                        # new_storage = False

                # current_storage = 0
                # current_bits = 0
                # new_storage = 'False'
                # extra = 0
                # ingress.write("                hdr.DINC_meta.storage" + str(current_storage) + " = ")
                # for m_idx, m in enumerate(config['D_P4_Info'][int(config['node index'])]['D_to_M'][idx]['output']):
                #     if current_bits + m[2] >= config['storage bits']:
                #         if new_storage == 'True':
                #             ingress.write("                hdr.DINC_meta.storage" + str(current_storage) + " = ")
                #             new_storage = 'False'
                #         ingress.write(
                #             "meta." + m[1] + "[" + str(config['storage bits'] - 1) + ":" + str(current_bits) + "];\n")
                #         current_storage += 1
                #         extra = m[2] - (config['storage bits'] - current_bits)
                #         current_bits = 0
                #         if extra > 0:
                #             ingress.write("                hdr.DINC_meta.storage" + str(current_storage) + " = ")
                #             if m_idx == len(
                #                     config['D_P4_Info'][int(config['node index'])]['D_to_M'][idx]['output']) - 1:
                #                 ingress.write("meta." + m[1] + "[" + str(current_bits + extra - 1) + ":" + str(
                #                     current_bits) + "];\n")
                #             else:
                #                 ingress.write("meta." + m[1] + "[" + str(current_bits + extra - 1) + ":" + str(
                #                     current_bits) + "] ++ ")
                #             current_bits += extra
                #             extra = 0
                #         else:
                #             new_storage = 'True'
                #         # print('d', config['node index'], 'current', current_bits)
                #
                #     else:
                #         if new_storage == 'True':
                #             ingress.write("                hdr.DINC_meta.storage" + str(current_storage) + " = ")
                #             new_storage = 'False'
                #         if m_idx == len(config['D_P4_Info'][int(config['node index'])]['D_to_M'][idx]['output']) - 1:
                #             ingress.write(
                #                 "meta." + m[1] + "[" + str(current_bits + m[2] - 1) + ":" + str(current_bits) + "];\n")
                #         else:
                #             ingress.write(
                #                 "meta." + m[1] + "[" + str(current_bits + m[2] - 1) + ":" + str(current_bits) + "] ++ ")
                #         current_bits += m[2]
                #         # print('d', config['node index'], 'current', current_bits)
                #         # new_storage = False
                ingress.write("            }\n\n")


        if config['D_P4_Info'][int(config['node index'])]['D_to_E']:
            ingress.write("        }\n\n")



