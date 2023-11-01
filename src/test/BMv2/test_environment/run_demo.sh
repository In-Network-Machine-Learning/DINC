#!/bin/bash
BMV2_PATH=/home/jesu3779/mysde/behavioral-model-1.15.0
SWITCH_PATH=$BMV2_PATH/targets/simple_switch/simple_switch
echo 'passcode' | sudo -S $SWITCH_PATH >/dev/null 2>&1
sudo make clean
sudo PYTHONPATH=$PYTHONPATH:$BMV2_PATH/mininet/ python3 main.py --behavioral-exe $SWITCH_PATH
