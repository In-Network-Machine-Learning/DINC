import matplotlib.pyplot as plt
import warnings
# warnings.filterwarnings('ignore')
import matplotlib
import numpy as np
import json
from math import sqrt



x = [2,3]
DINC = [33, 405]
flightplan = [ 51, 1901]

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
plt.ylabel('Duplications', fontsize=fsize)
plt.yscale('log')
plt.yticks([1,10,100,1000] ,fontsize=fsize-1)
plt.xticks(x, labels=['Clos', 'BT'], fontsize=fsize-1)
# plt.ylim(0.2,5000)
plt.ylim(0.1,10000)
plt.xlim(1.4,3.6)
leg = plt.legend(loc='lower center', fontsize=fsize-8)
plt.grid(which ='major',linestyle= ':', axis="y") #'major', 'minor'， 'both'
plt.savefig('../figures/DINC_Flightplan_Dup.pdf',dpi=600,format='pdf', bbox_inches='tight')

