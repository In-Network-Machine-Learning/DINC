import matplotlib.pyplot as plt
import warnings
# warnings.filterwarnings('ignore')
import matplotlib
import numpy as np
import json
from math import sqrt



x = [2,3]
DINC = [100*2/3, 100*3.11/3.81]
flightplan = [100*2/3 , 100*3.11/3.81]
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
plt.ylabel('Hops (%)', fontsize=fsize)
# plt.yscale('log')
# plt.yticks([0.2,0.4,0.6,0.8] ,fontsize=fsize-1)
plt.yticks([20,40,60,80] ,fontsize=fsize-1)
plt.xticks(x, labels=['Clos', 'BT'], fontsize=fsize-1)
# plt.ylim(0,1)
plt.ylim(0,100)
plt.xlim(1.4,3.6)  # 设置横坐标刻度为给定的年份
leg = plt.legend(loc='lower center', fontsize=fsize-8)
plt.grid(which ='major',linestyle= ':', axis="y") #'major', 'minor'， 'both'
plt.savefig('../figures/DINC_Flightplan_Hop.pdf',dpi=600,format='pdf', bbox_inches='tight')

