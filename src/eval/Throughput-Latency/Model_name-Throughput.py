import matplotlib.pyplot as plt
import warnings

# warnings.filterwarnings('ignore')
import matplotlib
import numpy as np
import json
from math import sqrt
# warnings.filterwarnings('ignore')



fsize =25

model = ['Seg0', 'Seg1', 'Seg2', 'Seg3' , 'RARE' ]
x = [1,2,3,4]

seg0 = (1596590+1596481+1596436+1596594)/1000000
seg1 = (1596392+1596402+1596475+1596385)/1000000
seg2 = (1596490+1596531+1596532+1596485)/1000000
seg3 = (1596242+1596400+1596387+1596204)/1000000

switch = (1596380+1596393+1596439+1596345)/1000000

ASIC = [seg0, seg1,seg2, seg3]

fig, ax = plt.subplots(figsize=(6, 3))
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
# plt.rcParams['font.sans-serif'] = 'Times New Roman'


plt.hlines(6.4,0,6, linestyle="--" , color = 'red')
plt.text(3.9, 6.6, 'Line rate', fontsize=fsize-1 , color = 'red')

width = 0.26
x_n = [i-0*width for i in x]
plt.bar(x_n,ASIC , width= width, label='Coexist with RARE',color = 'lightskyblue', linewidth = 1,edgecolor = 'black')


plt.bar([5],[switch] , width= width, label='Standalone RARE', color="silver",linewidth = 1,edgecolor = 'black')






# plt.grid(True) #'major', 'minor'， 'both'

# plt.xlabel('Model', fontsize=fsize) # 设置横坐标轴标题
plt.ylabel('Throughput', fontsize=fsize-1)
# plt.yscale('log')
plt.yticks([1.5,3,4.5,6], fontsize=fsize-1)
plt.xticks([1,2,3,4,5],labels=model,rotation=-20, fontsize=fsize-1)
plt.xlim(0.3,5.7)
plt.ylim(0,7.5)
plt.legend(loc='lower right', ncol=1, fontsize=fsize-8)
#

# plt.legend(bbox_to_anchor=(1.05, 0), loc=3,ncol=5, borderaxespad=0, fontsize=fsize)
plt.grid(which ='major', axis='y',linestyle= ':') #'major', 'minor' ， 'both'
plt.savefig('../figures/Segment-Throughput.pdf',dpi=600,format='pdf', bbox_inches='tight')
