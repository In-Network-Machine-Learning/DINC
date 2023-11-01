# This file is part of the Planter extend project: DINC.
# This program is a free software tool, which does ensemble in-network machine learning.
# licensed under Apache-2.0
#
# Copyright (c) 2020-2021 Changgang Zheng
# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford & Yale University
# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),
# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)


import numpy as np

def common_constants(fname, config):
    with open(fname, 'a') as headers:
        headers.write("const bit<16> TYPE_IPV4 = 0x800;\n\n"
                      # "const bit<16> ETHERTYPE_DINC = 0x1234;\n"
                      # "const bit<8>  DINC_P     = 0x50;   // 'P'\n"
                      # "const bit<8>  DINC_4     = 0x34;   // '4'\n"
                      # "const bit<8>  DINC_VER   = 0x01;   // v0.1\n"
                      "typedef bit<9> egressSpec_t;\n"
                      "typedef bit<48> macAddr_t;\n"
                      "typedef bit<32> ip4Addr_t;\n\n")



def common_metadata(fname, config):
    with open(fname, 'a') as headers:
        element_list = config['device to element'][config['node index']]
#         for e in element_list:
#             metadata = config['element metadata'][e][0] + ' ' + config['element metadata'][e][1]
#             headers.write("    "+  metadata + ";\n")



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

        # headers.write("header DINC_h{\n"
        #               "    bit<8> p;\n"
        #               "    bit<8> four;\n"
        #               "    bit<8> ver;\n"
        #               "    bit<8> typ;\n")
        #
        # for f in range(0, config['number storage']):
        #     headers.write("    bit<" + str(config["storage bits"]) + "> storage" + str(f) + ";\n")
        # headers.write("}\n\n")

        # write the headers' structure
        headers.write("struct header_t {\n"
                      "    ethernet_h   ethernet;\n"
                      "    ipv4_h       ipv4;\n"
                      # "    DINC_h       DINC;\n"
                      "}\n\n")


def common_parser(fname, config):
    with open(fname, 'a') as parser:
        parser.write("    state parse_ethernet {\n"
                     "        pkt.extract(hdr.ethernet);\n" 
                     "        transition select(hdr.ethernet.etherType) {\n" 
                     "            ETHERTYPE_DINC    : check_DINC_version;\n" 
                     "            TYPE_IPV4         : parse_ipv4;\n" 
                     "            default           : accept;\n" 
                     "        }\n" 
                     "    }\n\n")

        parser.write("    state parse_ipv4 {\n"
                     "        pkt.extract(hdr.ipv4);\n"
                     "        transition accept;\n"
                     "    }\n\n")


        # parser.write("    state check_DINC_version {\n"
        #              "        transition select(pkt.lookahead<DINC_h>().p,\n"
        #              "                          pkt.lookahead<DINC_h>().four,\n"
        #              "                          pkt.lookahead<DINC_h>().ver) {\n"
        #              "        (DINC_P, DINC_4, DINC_VER) : parse_DINC;\n"
        #              "        default                             : accept;\n"
        #              "        }\n"
        #              "    }\n\n" )


        # parser.write("    state parse_DINC {\n"
        #              "        pkt.extract(hdr.DINC);\n")
        # for f in range(0, config['number storage']):
        #     parser.write("        meta.feature" + str(f) + " = hdr.DINC.feature" + str(f) + ";\n")
        # parser.write("        meta.flag = 1 ;\n"
        #              "        transition accept;\n"
        #              "    }\n")

def common_tables(fname, config):
    with open(fname, 'a') as ingress:

        # ingress.write("    action send(bit<9> port) {\n"
        #               "        ig_intr_md.egress_spec = port;\n"
        #               "    }\n\n")

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

def common_logics(fname, config):
    with open(fname, 'a') as ingress:

        ingress.write("        if (hdr.ipv4.isValid() && hdr.ipv4.ttl > 0) {\n"
                      "            ipv4_lpm.apply();\n"
                      "        }\n\n")

        # for ax in range(0, config['num_axis']):
        #     ingress.write("        hdr.DINC.feature" + str(ax) + " = meta.feature" + str(ax) + ";\n")
        # ingress.write("        bit<48> tmp;\n"
        #               "        /* Swap the MAC addresses */\n"
        #               "        tmp = hdr.ethernet.dstAddr;\n"
        #               "        hdr.ethernet.dstAddr = hdr.ethernet.srcAddr;\n"
        #               "        hdr.ethernet.srcAddr = tmp;\n"
        #               "        send(ig_intr_md.ingress_port);\n")