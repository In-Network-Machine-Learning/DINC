import matplotlib.pyplot as plt
import warnings
# warnings.filterwarnings('ignore')
import matplotlib
import numpy as np
import json
from math import sqrt



x = [2,3]
# DINC = [30/33, 400/1008]
# flightplan = [30/33 , 971/1008]
DINC = [100*30/33, 100*400/1008]
flightplan = [100*30/33 , 100*971/1008]
fig, ax = plt.subplots(figsize=(3, 3))
# plt.rcParams['font.sans-serif'] = 'Times New Roman'
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
width = 0.3

x_n = [i-0.65*width for i in x]
plt.bar(x_n, flightplan,width=width, label='Flightplan', color="pink" ,linewidth = 1,edgecolor = 'black')

x_n = [i+0.65*width for i in x]
plt.bar(x_n, DINC, width= width, label='DINC', color="lightskyblue",linewidth = 1,edgecolor = 'black')

fsize =25
# plt.ylabel('Nodes', fontsize=fsize)
plt.ylabel('Nodes (%)', fontsize=fsize)
# plt.yscale('log')
# plt.yticks([0.2,0.4,0.6,0.8] ,fontsize=fsize-1)
plt.yticks([20,40,60,80] ,fontsize=fsize-1)
plt.xticks(x, labels=['Clos', 'BT'], fontsize=fsize-1)
# plt.ylim(0,1)
plt.ylim(0,100)
plt.xlim(1.4,3.6)
leg = plt.legend(loc='lower center', fontsize=fsize-8)
plt.grid(which ='major',linestyle= ':', axis="y") #'major', 'minor'， 'both'
plt.savefig('../figures/DINC_Flightplan_Node.pdf',dpi=600,format='pdf', bbox_inches='tight')

