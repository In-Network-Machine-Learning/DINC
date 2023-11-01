import matplotlib.pyplot as plt
import numpy as np
# import seaborn as sns


x = [1,2,3,4,5]
y1 = [0, 1, 1, 1, 1,]
y2 = [0, 1, 1, 1, 1,]
y3 = [0, 1, 1, 1, 1,]
y4 = [0, 1, 1, 1, 1,]
y5 = [0, 1, 1, 1, 1,]

y1 = [i*100 for i in y1]
y2 = [i*100 for i in y2]
y3 = [i*100 for i in y3]
y4 = [i*100 for i in y4]
y5 = [i*100 for i in y5]
distance = 0.03
x1 = x
x2 = [i-distance for i in x]
x3 = [i-2*distance for i in x]
x4 = [i+distance for i in x]
x5 = [i+2*distance for i in x]


fsize =25
lw=2
ms = 6
mes = 1
lw=2

fig, ax1 = plt.subplots(figsize=(5, 3))
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
# plt.rcParams['font.sans-serif'] = 'Times New Roman'
# plt.rcParams['mathtext.fontset']= 'custom'

plt.step(x1, y1, marker = 's',color="palevioletred",linewidth = lw , ms=ms, markeredgecolor='black', markeredgewidth=mes, where='post', label='Setup 1')
plt.step(x2, y2, marker = 'p',color="mediumseagreen",linewidth = lw , ms=ms, markeredgecolor='black', markeredgewidth=mes, where='post', label='Setup 2')
plt.step(x3, y3, marker = 'd',color="mediumslateblue",linewidth = lw , ms=ms, markeredgecolor='black', markeredgewidth=mes, where='post', label='Setup 3')
plt.step(x4, y4, marker = 'H',color="firebrick",linewidth = lw , ms=ms, markeredgecolor='black', markeredgewidth=mes, where='post', label='Setup 4')
plt.step(x5, y5, marker = '^',color="dodgerblue",linewidth = lw , ms=ms, markeredgecolor='black', markeredgewidth=mes, where='post', label='Setup 5')



plt.xlabel('Number of Hops', fontsize=fsize)  # 设置横坐标轴标题
plt.ylabel('CDF Percent (%)', fontsize=fsize)  # 设置横坐标轴标题



plt.yticks([ 0,30,60,90],   fontsize=fsize-1)  # 设置横坐标刻度为给定的年份
plt.xticks([1,2,3,4,5], fontsize=fsize-1)  # 设置横坐标刻度为给定的年份
plt.ylim(-15,115)  # 设置横坐标刻度为给定的年份
plt.xlim(0.5,5.5)  # 设置横坐标刻度为给定的年份
plt.legend(bbox_to_anchor=(1.05, 0), loc=3,ncol=5, labelspacing=0.4,columnspacing=0.4, borderaxespad=0, fontsize=fsize-8)
plt.grid(which ='major',linestyle= ':') #'major', 'minor' ， 'both'
plt.savefig('../figures/Setups_label.pdf',dpi=600,format='pdf', bbox_inches='tight')
