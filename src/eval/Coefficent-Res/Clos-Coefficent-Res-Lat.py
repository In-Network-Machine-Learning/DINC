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

# model = ['-2', '-1', '0', '1', '2']
# x = [-2, -1, 0, 1, 2]
# hops = [2, 3, 2, 2, 2]
# var = [0, 0, 0, 0, 0 ]
# segment = [45,15,42,42,42]
model = ['1', '2', '3', '4', '5']
x = [1, 2, 3, 4, 5]
hops = [3, 2, 2, 2, 2]
var = [0, 0, 0, 0, 0 ]
segment = [15, 45, 45, 45, 45]



fig, ax1 = plt.subplots(figsize=(5, 3))
ax2 = ax1.twinx()
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
# plt.rcParams['font.sans-serif'] = 'Times New Roman'
# plt.rcParams['mathtext.fontset']= 'custom'
width = 0.26
# cm stic stixsans custom
x_n = [i-0*width for i in x]
ax1.bar(x_n,hops ,width=width, label='Hops', color="lightskyblue" ,linewidth = 1,edgecolor = 'black' ,yerr=var, error_kw=dict(lw=1, capsize=2.5, capthick=1))



l1 = ax2.plot(x,  segment, '--', label='Segments', marker = 's', ms=ms, markeredgecolor='black', markeredgewidth=mes, color="#ff7f0e",linewidth = lw)




fsize+=2
plt.xlabel('Model', fontsize=fsize+1) # 设置横坐标轴标题
ax1.set_xticks(x) # 设置横坐标刻度为给定的年份
ax1.set_xticklabels(labels=model,rotation=-0, fontsize=fsize+1)
ax1.set_xlabel('Relative Weight', fontsize=fsize+1) # 设置横坐标轴标题

# ax1.set_yscale('log')
ax1.set_ylabel('Hops (s)', fontsize=fsize+1) # 设置横坐标轴标题
ax1.set_yticks([1,2,3,4]) # 设置横坐标刻度为给定的年份
ax1.set_yticklabels(labels=['1','2','3','4'], fontsize=fsize+1) # 设置横坐标刻度为给定的年份
ax1.set_ylim(0,5)  # 设置横坐标刻度为给定的年份


ax2.set_ylabel('Segments', fontsize=fsize+1) # 设置横坐标轴标题
ax2.set_yticks([25, 50, 75, 100]) # 设置横坐标刻度为给定的年份
ax2.set_yticklabels(labels=['25','50','75','100'], fontsize=fsize+1) # 设置横坐标刻度为给定的年份
ax2.set_ylim(0,125)  # 设置横坐标刻度为给定的年份


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
ax2.legend(f_line, f_lable, fancybox=True, fontsize=fsize-8,loc = "upper right", ncol=1)

plt.grid(which ='major',linestyle= ':') #'major', 'minor' ， 'both'
plt.savefig('../figures/Coefficent-hops_Clos.pdf',dpi=600,format='pdf', bbox_inches='tight')
# plt.show() # 显示图形
