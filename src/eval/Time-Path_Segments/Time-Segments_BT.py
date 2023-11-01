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




model = ['2', '3', '4', '5', '6']
x = [2,3,4,5,6]





# 2.585120415687561, 9.731816864013672, 16.573393726348876, 29.22371470928192, 56.68120107650757,
# 0.005196774484805836, 0.23781882269492483, 0.9169319803730787, 2.6102297522511937, 0.5890758830975283,
# 26512, 26512, 26512,26512,26512

time = [2.585120415687561, 9.731816864013672, 16.573393726348876, 29.22371470928192, 56.68120107650757]

var = [0.005196774484805836, 0.23781882269492483, 0.9169319803730787, 2.6102297522511937, 0.5890758830975283]


path = [26512, 26512, 26512,26512,26512]

fig, ax1 = plt.subplots(figsize=(5, 3))
ax2 = ax1.twinx()
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
# plt.rcParams['font.sans-serif'] = 'Times New Roman'
# plt.rcParams['mathtext.fontset']= 'custom'
width = 0.26
# cm stic stixsans custom
x_n = [i-0*width for i in x]
ax1.bar(x_n,time ,width=width, label='Time (s)', color="lightskyblue" ,linewidth = 1,edgecolor = 'black' ,yerr=var, error_kw=dict(lw=1, capsize=2.5, capthick=1))



l1 = ax2.plot(x,  path, '--', label='Paths', marker = 's', ms=ms, markeredgecolor='black', markeredgewidth=mes, color="#ff7f0e",linewidth = lw)




fsize+=2
plt.xlabel('Model', fontsize=fsize+1)
ax1.set_xticks(x)
ax1.set_xticklabels(labels=model,rotation=-0, fontsize=fsize+1)
ax1.set_xlabel('Num of Segments', fontsize=fsize+1)

ax1.set_yscale('log')
ax1.set_ylabel('Time (s)', fontsize=fsize+1)
ax1.set_yticks([10**-2,10**-1,10**-0,10**1])
ax1.set_yticklabels(labels=['10$^{-2}$','10$^{-1}$','10$^{-0}$','10$^{+1}$'], fontsize=fsize+1)
ax1.set_ylim(10**-3,10**2)


ax2.set_ylabel('Paths', fontsize=fsize+1)
ax2.set_yticks([8000,16000,24000,32000])
ax2.set_yticklabels(labels=['8k','16k','24k','32k'], fontsize=fsize+1)
ax2.set_ylim(0,40000)


plt.xlim(1.3,6.7)


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

plt.grid(which ='major',linestyle= ':') #'major', 'minor' ， 'both'
plt.savefig('../figures/Time_Segments_BT.pdf',dpi=600,format='pdf', bbox_inches='tight')
# plt.show()
