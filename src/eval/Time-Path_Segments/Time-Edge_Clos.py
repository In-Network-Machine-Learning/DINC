import matplotlib.pyplot as plt
import warnings
import matplotlib
import numpy as np
import json
from math import sqrt

fsize =25
lw=2
ms = 6
mes = 1
lw=2


# 输入纵坐标轴数据与横坐标轴数据

model = ['1', '2', '3', '4', '5']
x = [1,2,3,4,5]

# 0.10952112674713135, 0.12678711414337157, 0.13884289264678956, 0.16474764347076415, 0.17274291515350343]
# 0.0032471952915711067, 0.0006922912296972685, 0.001049483076647019, 0.004338363073341647, 0.0010001896391073721]
# 36,72,108,140,172


time = [0.0030060768127441405, 0.004389834403991699, 0.005976200103759766, 0.007393336296081543, 0.008810830116271973]

var = [0.00021867281575554406, 0.00019698073314995026, 0.0003215019508841349, 0.0002193663278438717, 0.00029543081091567815]


path = [18,36,54,72,90]

fig, ax1 = plt.subplots(figsize=(5, 3))
ax2 = ax1.twinx()
# plt.rcParams['font.sans-serif'] = 'Times New Roman'
# plt.rcParams['mathtext.fontset']= 'custom'
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
width = 0.26
# cm stic stixsans custom
x_n = [i-0*width for i in x]
ax1.bar(x_n,time ,width=width, label='Time (s)', color="lightskyblue" ,linewidth = 1,edgecolor = 'black' ,yerr=var, error_kw=dict(lw=1, capsize=2.5, capthick=1))



l1 = ax2.plot(x,  path, '--', label='Paths', marker = 's', ms=ms, markeredgecolor='black', markeredgewidth=mes, color="#ff7f0e",linewidth = lw)




fsize+=2
plt.xlabel('Model', fontsize=fsize+1) # 设置横坐标轴标题
ax1.set_xticks(x) # 设置横坐标刻度为给定的年份
ax1.set_xticklabels(labels=model,rotation=-0, fontsize=fsize+1)
ax1.set_xlabel('Num of Edge Nodes', fontsize=fsize+1) # 设置横坐标轴标题

ax1.set_yscale('log')
ax1.set_ylabel('Time (s)', fontsize=fsize+1) # 设置横坐标轴标题
ax1.set_yticks([10**-3,10**-2,10**-1,10**0]) # 设置横坐标刻度为给定的年份
ax1.set_yticklabels(labels=['10$^{-3}$','10$^{-2}$','10$^{-1}$','10$^{-0}$'], fontsize=fsize+1) # 设置横坐标刻度为给定的年份
ax1.set_ylim(10**-4,10**1)  # 设置横坐标刻度为给定的年份


ax2.set_ylabel('Paths', fontsize=fsize+1) # 设置横坐标轴标题
ax2.set_yticks([50,100,150,200]) # 设置横坐标刻度为给定的年份
ax2.set_yticklabels(labels=['30','50','70','90'], fontsize=fsize+1) # 设置横坐标刻度为给定的年份
ax2.set_ylim(0,250)  # 设置横坐标刻度为给定的年份


plt.xlim(0.3,5.7)  # 设置横坐标刻度为给定的年份


lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
f_line = lines + lines2
# f_line[1] = lines[0]
# f_line[0] = lines2[0]
# f_line[3] = lines[1]
# f_line[2] = lines2[1]
f_lable = labels + labels2
# f_lable[1] = labels[0]
# f_lable[0] = labels2[0]
# f_lable[3] = labels[1]
# f_lable[2] = labels2[1]
ax2.legend(f_line, f_lable, fancybox=True, fontsize=fsize-8,loc = "upper left", ncol=1)

plt.grid(which ='major',  linestyle= ':') #'major', 'minor' ， 'both'
plt.savefig('../figures/Time-Edge_clos.pdf',dpi=600,format='pdf', bbox_inches='tight')
# plt.show() # 显示图形
