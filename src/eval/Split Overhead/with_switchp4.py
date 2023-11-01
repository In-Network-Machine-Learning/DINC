import matplotlib.pyplot as plt
import warnings
# warnings.filterwarnings('ignore')
import matplotlib
import numpy as np
import json
from math import sqrt



x = [2,3]

DINC = [11, 12]
standalone = [11 , 11]
fig, ax = plt.subplots(figsize=(3, 3))
# plt.rcParams['font.sans-serif'] = 'Times New Roman'
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
width = 0.3

x_n = [i-0.65*width for i in x]
plt.bar(x_n, standalone,width=width, label='Switch.p4', color="pink" ,linewidth = 1,edgecolor = 'black')

x_n = [i+0.65*width for i in x]
plt.bar(x_n, DINC, width= width, label='Seg.+Switch.p4', color="lightskyblue",linewidth = 1,edgecolor = 'black')

fsize =25
# plt.ylabel('Nodes', fontsize=fsize)
plt.ylabel('Stage', fontsize=fsize)
# plt.yscale('log')
# plt.yticks([0.2,0.4,0.6,0.8] ,fontsize=fsize-1)
plt.yticks([9,10,11,12] ,fontsize=fsize-1)
plt.xticks(x, labels=['Node 1', 'Node 2'], fontsize=fsize-1)
# plt.ylim(0,1)
plt.ylim(8,13)
plt.xlim(1.4,3.6)
leg = plt.legend(loc='lower center', fontsize=fsize-8, handlelength=1)
plt.grid(which ='major',linestyle= ':', axis="y") #'major', 'minor'， 'both'
plt.savefig('../figures/Split_stage_with_switch_p4.pdf',dpi=600,format='pdf', bbox_inches='tight')

