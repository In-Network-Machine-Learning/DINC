import matplotlib.pyplot as plt
import warnings

# warnings.filterwarnings('ignore')
import matplotlib
import numpy as np
import json
from math import sqrt
# warnings.filterwarnings('ignore')


titles=[]
latency=[]
srams=[]
tcams=[]
memory=[]

config = {}
config['list of files'] = []
config['list of files'] += [['sample', './Logs/switch_p4_metrics.json']]
config['list of files'] +=[['seg0', './Logs/metrics0.json']]
config['list of files'] +=[['seg1', './Logs/metrics1.json']]
config['list of files'] +=[['seg2', './Logs/metrics2.json']]
config['list of files'] +=[['seg3', './Logs/metrics3.json']]
config['list of files'] +=[['switch', './Logs/metrics_switch.json']]

for i in range(0,len(config['list of files'])):
    titles.append(config['list of files'][i][0])
    resources=json.load(open(config['list of files'][i][1],'r'))
#	print(resources['mau']['latency'][0]['cycles'])
    if (i==0):
        srams.append(1)
        tcams.append(1)
        sram_baseline=int(resources['mau']['srams'])
        tcam_baseline=int(resources['mau']['tcams'])
        memory.append(1)
        latency.append(1)
        latency_baseline=int(resources['mau']['latency'][0]['cycles'])
    else:
        sram=int(resources['mau']['srams'])/sram_baseline
        srams.append(sram)
        tcam=int(resources['mau']['tcams'])/tcam_baseline
        tcams.append(tcam)
        mems=(sram+tcam)/2
        memory.append(mems)
        lat=int(resources['mau']['latency'][0]['cycles'])/latency_baseline
        latency.append(lat)
        print("App: "+config['list of files'][i][0]+" Latency: "+str(lat)+" Memory: "+str(mems)+" SRAM: "+str(sram)+" TCAM: "+str(tcam))



model = ['Seg0', 'Seg1', 'Seg2', 'Seg3' , 'RARE' ]
x = [1,2,3,4]

seg0 = latency[1]*100
seg1 = latency[2]*100
seg2 = latency[3]*100
seg3 = latency[4]*100

switch = latency[5]*100

ASIC = [seg0, seg1,seg2, seg3]

fig, ax = plt.subplots(figsize=(6.2, 3))
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
# plt.rcParams['font.sans-serif'] = 'Times New Roman'
width = 0.26

x_n = [i-0*width for i in x]
plt.bar(x_n,ASIC , width= width, label='Coexist with RARE',color = 'lightskyblue', linewidth = 1,edgecolor = 'black')


plt.bar([5],[switch] , width= width, label='Standalone RARE', color="silver",linewidth = 1,edgecolor = 'black')




fsize =25


# plt.grid(True) #'major', 'minor'， 'both'

# plt.xlabel('Model', fontsize=fsize) # 设置横坐标轴标题
plt.ylabel('R-Latency (%)', fontsize=fsize)
# plt.yscale('log')
plt.yticks([15,30,45,60], fontsize=fsize-1)
plt.xticks([1,2,3,4,5],labels=model,rotation=-20, fontsize=fsize-1)
plt.xlim(0.3,5.7)
plt.ylim(0,75)
plt.legend(loc='lower right', ncol=1, fontsize=fsize-8)
#

# plt.legend(bbox_to_anchor=(1.05, 0), loc=3,ncol=5, borderaxespad=0, fontsize=fsize)
plt.grid(which ='major', axis='y',linestyle= ':') #'major', 'minor' ， 'both'
plt.savefig('../figures/Segment-Latency.pdf',dpi=600,format='pdf', bbox_inches='tight')
