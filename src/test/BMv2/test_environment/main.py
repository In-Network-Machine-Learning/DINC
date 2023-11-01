# This file is part of the Planter extend project: DINC.
# This program is a free software tool, which does ensemble in-network machine learning.
# licensed under Apache-2.0
#
# Copyright (c) 2020-2021 Changgang Zheng
# Copyright (c) Computing Infrastructure Group, Department of Engineering Science, University of Oxford & Yale University
# E-mail: changgang.zheng@eng.ox.ac.uk (valid until July 2024),
# changgang.zheng@yale.edu (valid until October 2022) or changgangzheng@qq.com (no expiration date)

# from p4app import P4Mininet, P4Program
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../utils/'))

from p4_mininet import P4Switch, P4Host

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink

import json
import argparse
from time import sleep
import subprocess

_THIS_DIR = os.path.dirname(os.path.realpath(__file__))
_THRIFT_BASE_PORT = 9090

build_dir = './build'
os.makedirs(build_dir, exist_ok=True)

parser = argparse.ArgumentParser(description='Mininet demo')
parser.add_argument('--behavioral-exe', help='Path to behavioral executable',
                    type=str, action="store", required=True)

args = parser.parse_args()


BMv2_network_config = json.load(open('./temp/BMv2_network_config.json', 'r', encoding = 'utf-8'))
# n = 3
#
# basic_prog = P4Program('basic.p4')
# wire_prog = P4Program('wire.p4')

class DINC_topology(Topo):
    def __init__(self, sw_path, BMv2_network_config, **opts):
        Topo.__init__(self, **opts)

        switches = []

        for id in BMv2_network_config['switch id']:
            # print(int(id),id)
            program_id = BMv2_network_config['switch to P4 file'][str(id)]
            program = program_id.split('/')[2].split('.')[0]
            # print('program_id ', program_id)
            # print('program ', program)
            json_file = './build/' + program + '.json'
            info_file = './build/' + program + '.p4info.txt'
            os.system("p4c-bm2-ss --std p4-16 ./P4/%s.p4 -o %s --p4runtime-files %s" % (program, json_file, info_file))
            # switch = self.addSwitch('s%d' % int(id), program=program)
            switch = self.addSwitch('s%d' % int(id),
                                    sw_path = sw_path,
                                    json_path = json_file,
                                    #program=program,
                                    thrift_port = _THRIFT_BASE_PORT + int(id),
                                    pcap_dump = False,
                                    device_id = int(id))
            switches.append(switch)
            if int(id) in BMv2_network_config['switch to server']:
                if int(id) != 0:
                    host = self.addHost('h%d' % (int(id)),
                                        ip="10.0.0.%d" % (int(id)),
                                        mac='10:00:00:00:00:%02x' % (int(id)))
                else:
                    host = self.addHost('h%d' % (int(id)),
                                        ip="10.0.0.%d" % (254),
                                        mac='10:00:00:00:00:%02x' % (int(id)))
                self.addLink(host, switch, port2=88)


        # Port 2 connects to the next switch in the ring, and port 3 to the previous
        print(switches)
        for pair in BMv2_network_config['switch to switch']:
            i_switch = BMv2_network_config['switch to switch'][pair][0]
            j_switch = BMv2_network_config['switch to switch'][pair][1]
            i_port = int(BMv2_network_config['switch port'][pair][0])
            j_port =  int(BMv2_network_config['switch port'][pair][1])
            print(i_switch,j_switch,switches[i_switch], switches[j_switch],i_port,j_port)
            self.addLink(switches[i_switch], switches[j_switch], port1=i_port, port2=j_port)




def main():
    topo = DINC_topology(args.behavioral_exe, BMv2_network_config)
    # net = P4Mininet(program=P4Program(''), topo=topo)
    net = Mininet(topo = topo,
                  host = P4Host,
                  switch = P4Switch,
                  controller = None,
                  autoStaticArp=True )
    net.start()
    for n in BMv2_network_config['switch id']:
        if int(n) in BMv2_network_config['switch to server']:
            h = net.get('h%d' % (int(n)))
            for off in ["rx", "tx", "sg"]:
                cmd = "/sbin/ethtool --offload eth0 %s off" % off
                print(cmd)
                h.cmd(cmd)
            print("disable ipv6")
            h.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
            h.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
            h.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")
            h.cmd("sysctl -w net.ipv4.tcp_congestion_control=reno")
            h.cmd("iptables -I OUTPUT -p icmp --icmp-type destination-unreachable -j DROP")
        # h.setIP("10.0.0.%d" % int(n))
        # h.setMAC("aa:bb:cc:dd:ee:0%d" % int(n))
        # for i in BMv2_network_config['switch id']:
        #     if (i != int(n)):
        #         h.setARP("10.0.0.%d" % int(i), "aa:bb:cc:dd:ee:0%d" % int(i))
        # #net.get('s1').setMAC("aa:bb:cc:dd:ee:1%d" % (n + 1), "s1-eth%d" % (n + 1))


    sleep(1)

    #for i in range(nb_switches):
    #    #cmd = [args.cli, "--json", args.json, "--thrift-port", str(_THRIFT_BASE_PORT + i)]
    #    cmd = [args.cli, args.json, str(_THRIFT_BASE_PORT + i)]
    #    with open("commands.txt", "r") as f:
    #        print(" ".join(cmd))
    #        try:
    #            output = subprocess.check_output(cmd, stdin = f)
    #            print(output)
    #        except subprocess.CalledProcessError as e:
    #            print(e)
    #            print(e.output)

    # for i in BMv2_network_config['switch id']:
    #     sw = net.get('s%d'% int(i))
    #
    #     # Forward to the host connected to this switch
    #     sw.insertTableEntry(table_name='MyIngress.ipv4_lpm',
    #                         match_fields={'hdr.ipv4.dstAddr': ["10.0.0.%d" % int(i), 32]},
    #                         action_name='MyIngress.ipv4_forward',
    #                         action_params={'dstAddr': '00:00:00:00:00:%02x' % int(i),
    #                                           'port': 1})
    #
    #     # Otherwise send the packet clockwise
    #     sw.insertTableEntry(table_name='MyIngress.ipv4_lpm',
    #                         default_action=True,
    #                         action_name='MyIngress.ipv4_forward',
    #                         action_params={'dstAddr': '00:00:00:00:00:00', # the last hop will set this correctly
    #                                           'port': 2})

    sleep(1)


    print("Ready !")
    os.system('bash insert_rules.sh')

    CLI( net )



if __name__ == '__main__':
    setLogLevel( 'info' )
    main()
