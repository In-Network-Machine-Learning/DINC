########################################################################
# THIS FILE IS PART OF Planter PROJECT
# Copyright (c) Changgang Zheng and Computing Infrastructure Lab
# Departement of Engineering Science, University of Oxford
# All rights reserved.
# E-mail: changgang.zheng@eng.ox.ac.uk or changgangzheng@qq.com
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at :
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#########################################################################
# This file was autogenerated

/*
 * Planter
 *
 * This program implements a simple protocol. It can be carried over Ethernet
 * (Ethertype 0x1234).
 *
 * The Protocol header looks like this:
 *
 *        0                1                  2              3
 * +----------------+----------------+----------------+---------------+
 * |      P         |       4        |     Version    |     Type      |
 * +----------------+----------------+----------------+---------------+
 * |                              feature0                            |
 * +----------------+----------------+----------------+---------------+
 * |                              feature1                            |
 * +----------------+----------------+----------------+---------------+
 * |                              feature2                            |
 * +----------------+----------------+----------------+---------------+
 * |                              feature3                            |
 * +----------------+----------------+----------------+---------------+
 * |                              Result                              |
 * +----------------+----------------+----------------+---------------+
 *
 * P is an ASCII Letter 'P' (0x50)
 * 4 is an ASCII Letter '4' (0x34)
 * Version is currently 1 (0x01)
 * Type is currently 1 (0x01)
 *
 * The device receives a packet, do the classification, fills in the
 * result and sends the packet back out of the same port it came in on, while
 * swapping the source and destination addresses.
 *
 * If an unknown operation is specified or the header is not valid, the packet
 * is dropped
 */

#include <core.p4>
# include <spectrum_model.p4>
# include <spectrum_externs.p4>
# include <spectrum_headers.p4>
# include <spectrum_parser.p4>

/*************************************************************************
*********************** headers and metadata *****************************
*************************************************************************/

const bit<16> ETHERTYPE_Planter = 0x1234;
const bit<8>  Planter_P     = 0x50;   // 'P'
const bit<8>  Planter_4     = 0x34;   // '4'
const bit<8>  Planter_VER   = 0x01;   // v0.1
header ethernet_h {
    bit<48> dstAddr;
    bit<48> srcAddr;
    bit<16> etherType;
}

header Planter_h{
    bit<8> p;
    bit<8> four;
    bit<8> ver;
    bit<8> typ;
    bit<32> feature0;
    bit<32> feature1;
    bit<32> feature2;
    bit<32> feature3;
    bit<32> result;
}

struct header_t {
    ethernet_h   ethernet;
    Planter_h    Planter;
}

struct metadata_t {
    bit<1> code_f0;
    bit<2> code_f1;
    bit<3> code_f2;
    bit<3> code_f3;
    bit<7> sum_prob;
    bit<32>  DstAddr;
    bit<32> feature0;
    bit<32> feature1;
    bit<32> feature2;
    bit<32> feature3;
    bit<32> result;
    bit<8> flag ;
}

/*************************************************************************
*********************** Ingress Parser ***********************************
*************************************************************************/

parser SwitchParser(
    packet_in pkt,
    out header_t hdr,
    inout metadata_t meta,
    inout standard_metadata_t ig_intr_md) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        pkt.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
        ETHERTYPE_Planter : check_planter_version;
        default           : accept;
        }
    }

    state check_planter_version {
        transition select(pkt.lookahead<Planter_h>().p,
                          pkt.lookahead<Planter_h>().four,
                          pkt.lookahead<Planter_h>().ver) {
        (Planter_P, Planter_4, Planter_VER) : parse_planter;
        default                             : accept;
        }
    }

    state parse_planter {
        pkt.extract(hdr.Planter);
        meta.feature0 = hdr.Planter.feature0;
        meta.feature1 = hdr.Planter.feature1;
        meta.feature2 = hdr.Planter.feature2;
        meta.feature3 = hdr.Planter.feature3;
        meta.flag = 1 ;
        transition accept;
    }
}

/*************************************************************************
*********************** Egress Deparser *********************************
**************************************************************************/

control SwitchDeparser(
    packet_out pkt,
    in header_t hdr) {
    apply {
        pkt.emit(hdr);
    }
}

/*************************************************************************
*********************** Ingress Processing********************************
**************************************************************************/

control SwitchIngress(
    inout header_t hdr,
    inout metadata_t meta,
    inout standard_metadata_t ig_intr_md) {

    action send(bit<9> port) {
        ig_intr_md.egress_spec = port;
    }

    action drop() {
        mark_to_drop(ig_intr_md);
    }

    // dependency marker @!slice, 0!@  m-@!position, control!@
    action extract_feature0(out bit<1> meta_code, bit<1> tree){
        meta_code = tree;
    }
    // dependency marker @!end,0!@



    // dependency marker @!slice, 0!@  m-@!position, control!@
    action extract_feature1(out bit<2> meta_code, bit<2> tree){
        meta_code = tree;
    }





    table lookup_feature0 {
        key = { meta.feature0:ternary; }
        actions = {
            extract_feature0(meta.code_f0);
            NoAction;
            }
        size = 8;
        default_action = NoAction;
    }

    table lookup_feature1 {
        key = { meta.feature1:ternary; }
        actions = {
            extract_feature1(meta.code_f1);
            NoAction;
            }
        size = 7;
        default_action = NoAction;
    }
    // dependency marker @!end,0!@



    // dependency marker @!slice, 1!@  @!position, control!@



    action extract_feature2(out bit<3> meta_code, bit<3> tree){
        meta_code = tree;
    }

    action extract_feature3(out bit<3> meta_code, bit<3> tree){
        meta_code = tree;
    }


    table lookup_feature2 {
        key = { meta.feature2:ternary; }
        actions = {
            extract_feature2(meta.code_f2);
            NoAction;
            }
        size = 15;
        default_action = NoAction;
    }

    table lookup_feature3 {
        key = { meta.feature3:ternary; }
        actions = {
            extract_feature3(meta.code_f3);
            NoAction;
            }
        size = 10;
        default_action = NoAction;
    }

    // dependency marker @!end,1!@




    // dependency marker m-@!slice, 2!@  m-@!position, control!@



    action write_default_class() {
        meta.result = 1;
    }

    action read_lable(bit<32> label){
        meta.result = label;
    }

    table decision {
        key = { meta.code_f0[0:0]:exact;
                meta.code_f1[1:0]:exact;
                meta.code_f2[2:0]:exact;
                meta.code_f3[2:0]:exact;
                }
        actions={
            read_lable;
            write_default_class;
        }
        size = 13;
        default_action = write_default_class;
    }
    // dependency marker @!end,2!@


    apply{
        // dependency marker @!slice, 0!@ @!previous, none!@ m-@!position, control-apply!@
        // resource marker @!stage, 5!@ @!memory, 5!@
        // p4 marker @!metadata_in, bit<32>, feature0!@ @!metadata_in, bit<32>, feature1!@
        // p4 marker @!metadata_out, bit<1>, code_f0!@ @!metadata_out, bit<2>, code_f1!@
        lookup_feature0.apply();
        lookup_feature1.apply();
        // dependency marker @!end,0!@

        // dependency marker @!slice,1!@ @!previous,0!@ @!position, control-apply!@
        // resource marker @!stage, 5!@ @!memory, 5!@
        // p4 marker @!metadata_in, bit<32>, feature2!@ @!metadata_in, bit<32>, feature3!@
        // p4 marker @!metadata_out, bit<3>, code_f2!@ @!metadata_out, bit<3>, code_f3!@
        lookup_feature2.apply();
        lookup_feature3.apply();
        // dependency marker @!end,1!@

        // dependency marker m-@!slice,2!@ @!previous,0,1!@ m-@!position, control-apply!@
        // resource marker @!stage, 5!@ @!memory, 5!@
        // p4 marker @!metadata_in, bit<1>, code_f0!@ @!metadata_in, bit<2>, code_f1!@ @!metadata_in, bit<3>, code_f2!@ @!metadata_in, bit<3>, code_f3!@
        // p4 marker @!metadata_out, bit<32>, result!@
        decision.apply();
        // dependency marker @!end,2!@


        send(ig_intr_md.ingress_port);
    }
}
/*************************************************************************
***********************  S W I T C H  ************************************
*************************************************************************/

NvSpectrumTunnelPipeline(
    SwitchIngressParser(),
    SwitchIngress(),
    SwitchEgressDeparser()
) main;
