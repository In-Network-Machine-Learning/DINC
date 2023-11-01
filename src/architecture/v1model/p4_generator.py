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
import numpy as np
from common_p4 import *
from src.functions.add_license import *
from src.functions.config_modification import *
from src.functions.write_file import *


def create_constants(fname, config):
    with open(fname, 'a') as headers:
        headers.write("/*************************************************************************\n"
                     "***************************** constants **********************************\n"
                     "*************************************************************************/\n\n")
    common_constants(fname, config)

def create_headers(fname, config):
    with open(fname, 'a') as headers:
        headers.write("/*************************************************************************\n"
                     "****************************** headers ***********************************\n"
                     "*************************************************************************/\n\n")
    common_headers(fname, config)


def create_metadata(fname, config):
    with open(fname, 'a') as metadata:
        metadata.write("/*************************************************************************\n"
                      "***************************** metadata **********************************\n"
                      "*************************************************************************/\n\n")

    with open(fname, 'a') as metadata:
        metadata.write("struct metadata_t {\n")

    try:
        separate_metadata(fname, config)
    except Exception as e:
        pass
    try:
        common_metadata(fname, config)
    except Exception as e:
        print(e)
        pass
    with open(fname, 'a') as metadata:
        metadata.write("}\n\n")
###################################################
# Create a parser file to be used
# input: parser file name, configuration
# output: none
###################################################

# This code currently does not support skipping columns. This is to be added once the basic functionality is tested
def create_parser(fname, config):

    with open(fname, 'a') as parser:

        parser.write("/*************************************************************************\n"
                     "*********************** Ingress Parser ***********************************\n"
                     "*************************************************************************/\n\n")



        parser.write(
            "parser SwitchParser(\n"
            "    packet_in pkt,\n"
            "    out header_t hdr,\n"
            "    inout metadata_t meta,\n"
            "    inout standard_metadata_t ig_intr_md) {\n\n")

        parser.write("    state start {\n"
                     "        transition parse_ethernet;\n"
                     "    }\n\n")

    common_parser(fname, config)

    with open(fname, 'a') as parser:
        parser.write("}\n\n")

        parser.write("/*************************************************************************\n"
                     "*********************** Egress Deparser *********************************\n"
                     "**************************************************************************/\n\n")

        parser.write("control SwitchDeparser(\n"
                     "    packet_out pkt,\n"
                     "    in header_t hdr) {\n"
                     "    apply {\n"
                     "        pkt.emit(hdr);\n"
                     "    }\n"
                     "}\n\n")




        parser.write("/*************************************************************************\n"
                     "********************** Checksum Verification *****************************\n"
                     "*************************************************************************/\n\n")
        parser.write(
            "control SwitchVerifyChecksum(inout header_t hdr,\n"
            "                       inout metadata_t meta) {\n"
            "    apply {}\n"
            "}\n")


        parser.write("/*************************************************************************\n"
                     "********************** Checksum Computation ******************************\n"
                     "*************************************************************************/\n\n")
        parser.write(
            "control SwitchComputeChecksum(inout header_t hdr,\n"
            "                        inout metadata_t meta) {\n"
            "    apply {\n"
            "        update_checksum(\n"
            "            hdr.ipv4.isValid(),\n"
            "            { hdr.ipv4.version,\n"
            "              hdr.ipv4.ihl,\n"
            "              hdr.ipv4.diffserv,\n"
            "              hdr.ipv4.totalLen,\n"
            "              hdr.ipv4.identification,\n"
            "              hdr.ipv4.flags,\n"
            "              hdr.ipv4.fragOffset,\n"
            "              hdr.ipv4.ttl,\n"
            "              hdr.ipv4.protocol,\n"
            "              hdr.ipv4.srcAddr,\n"
            "              hdr.ipv4.dstAddr },\n"
            "            hdr.ipv4.hdrChecksum,\n"
            "            HashAlgorithm.csum16);\n"
            "        }\n"
            "}\n")



###################################################
# Create an ingress control file
# input: ingress_control file name, configuration
# output: none
###################################################

# This code currently does not support skipping columns. This is to be added once the basic functionality is tested
def create_ingress_control(fname, config):

    with open(fname, 'a') as ingress:

        ingress.write("/*************************************************************************\n"
                      "*********************** Ingress Processing********************************\n"
                      "**************************************************************************/\n\n")

        ingress.write("control SwitchIngress(\n    inout header_t hdr,\n"
                      "    inout metadata_t meta,\n"
                      "    inout standard_metadata_t ig_intr_md) {\n\n")



    # =================== Tables and actions =================
    try:
        common_tables(fname, config)
    except Exception as e:
        pass
    try:
        separate_tables(fname, config)
    except Exception as e:
        pass



    with open(fname, 'a') as ingress:
        ingress.write("    apply{\n")

    # =================== Logics =================
    try:
        common_feature_extraction(fname, config)
    except Exception as e:
        pass
    try:
        separate_logics(fname, config)
    except Exception as e:
        pass
    try:
        common_logics(fname, config)
    except Exception as e:
        pass


    with open(fname, 'a') as ingress:
        ingress.write("    }\n" )
        ingress.write("}\n")


###################################################
# Create an egress control file
# input: egress_control file name, configuration
# output: none
###################################################

# This code currently does not support skipping columns. This is to be added once the basic functionality is tested
def create_egress_control(fname, config):

    with open(fname, 'a') as egress:
        egress.write("/*************************************************************************\n"
                     "*********************** egress Processing********************************\n"
                     "**************************************************************************/\n\n"
                     "control SwitchEgress(inout header_t hdr,\n"
                     "    inout metadata_t meta,\n"
                     "    inout standard_metadata_t eg_intr_md) {\n")

        # The following implements static routing between two ports, change as necessary
        egress.write("    apply {\n"
                     )

        egress.write("    }\n}\n")


###################################################
# Create main function in p4 code
# input: table scipt file name, tables data json file name, configuration
# output: none
###################################################
def create_main(fname, config):
    with open(fname, 'a') as main:
        main.write("/*************************************************************************\n"
                     "***********************  S W I T C H  ************************************\n"
                     "*************************************************************************/\n\n"
                     "V1Switch(\n"
                     "    SwitchParser(),\n"
                     "    SwitchVerifyChecksum(),\n"
                     "    SwitchIngress(),\n"
                     "    SwitchEgress(),\n"
                     "    SwitchComputeChecksum(),\n"
                     "    SwitchDeparser()\n"
                     ") main;")


###################################################
# Create includes in code
# input: table scipt file name, tables data json file name, configuration
# output: none
###################################################

def create_include(fname, config):
    with open(fname, 'a') as main:
        main.write("#include <core.p4>\n")
        main.write("#include <v1model.p4>\n\n")




##################################################
# Main function
# Parse input, set file name and call functions
##################################################

def generate_p4(Allocation, DINC_config, config, p4_file):
    add_license(p4_file)
    # create include file
    create_include(p4_file, config)
    # create constant defination file
    create_constants(p4_file, config)
    # create headers file
    create_headers(p4_file, config)
    # create metadata file
    create_metadata(p4_file, config)
    # create ingress parser
    create_parser(p4_file, config)
    # create ingress control
    create_ingress_control(p4_file, config)
    # create egress control
    create_egress_control(p4_file, config)
    # create main function
    create_main(p4_file, config)
    # print('The p4 file is generated')

    ##################################################

    print("Done")




