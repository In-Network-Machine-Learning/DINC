import matplotlib.pyplot as plt
import warnings
# warnings.filterwarnings('ignore')
import matplotlib
import numpy as np
import json
from math import sqrt



x = [2,3]

DINC = [3 , 5]
standalone = [2, 4]
fig, ax = plt.subplots(figsize=(3, 3))
# plt.rcParams['font.sans-serif'] = 'Times New Roman'
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
width = 0.3

x_n = [i-0.65*width for i in x]
plt.bar(x_n, standalone,width=width, label='Seg. Ideal', color="pink" ,linewidth = 1,edgecolor = 'black')

x_n = [i+0.65*width for i in x]
plt.bar(x_n, DINC, width= width, label='Seg. DINC', color="lightskyblue",linewidth = 1,edgecolor = 'black')

fsize =25
# plt.ylabel('Nodes', fontsize=fsize)
plt.ylabel('Stage', fontsize=fsize)
# plt.yscale('log')
# plt.yticks([0.2,0.4,0.6,0.8] ,fontsize=fsize-1)
plt.yticks([1.5,2.5,3.5,4.5] ,fontsize=fsize-1)
plt.xticks(x, labels=['Node 1', 'Node 2'], fontsize=fsize-1)
# plt.ylim(0,1)
plt.ylim(0.5,5.5)
plt.xlim(1.4,3.6)
# leg = plt.legend(loc='lower center', fontsize=fsize-8, handlelength=1)
leg = plt.legend(loc='lower center', fontsize=fsize-8)
plt.grid(which ='major',linestyle= ':', axis="y") #'major', 'minor'， 'both'
plt.savefig('../figures/Split_stage.pdf',dpi=600,format='pdf', bbox_inches='tight')

