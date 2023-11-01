import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import cartopy.feature as cfeature
from matplotlib.offsetbox import AnchoredText
from load_BT import *
from convertbng.util import convert_bng, convert_lonlat
import time

rotated_pole = ccrs.RotatedPole(pole_latitude=45, pole_longitude=180)

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1, projection=rotated_pole)
ax.set_extent([-10.2, 2, 49.5, 59.5], crs=ccrs.PlateCarree())
# ax.add_feature(cfeature.LAND)
# ax.add_feature(cfeature.OCEAN)
# ax.add_feature(cfeature.COASTLINE)
# ax.add_feature(cfeature.BORDERS, linestyle=':')
# ax.add_feature(cfeature.LAKES, alpha=0.5)
# ax.add_feature(cfeature.RIVERS)
# stamen_terrain = cimgt.Stamen('terrain-background')
# ax.add_image(stamen_terrain, 6)
# stamen_terrain = cimgt.Stamen('toner-hybrid')
# ax.add_image(stamen_terrain, 6)
# stamen_terrain = cimgt.Stamen('toner-lite')
# ax.add_image(stamen_terrain, 6)
# stamen_terrain = cimgt.Stamen('toner-lines')
# ax.add_image(stamen_terrain, 6)
# stamen_terrain = cimgt.Stamen('toner-labels')
# ax.add_image(stamen_terrain, 6)
# ax.gridlines(draw_labels=False, dms=True, x_inline=False, y_inline=False)
# Put a background image on for nice sea rendering.
# ax.stock_img()



D, adjacent_matrix, Level_dict = load_data(Reload=True)
num_d = len(D.keys())
x_lon_list = []
x_lat_list = []

x_oc_lon_list = []
x_oc_lat_list = []

x_ic_lon_list = []
x_ic_lat_list = []

x_metro_lon_list = []
x_metro_lat_list = []

x_tier1_lon_list = []
x_tier1_lat_list = []

for x in range(num_d):
    print('\rProcessing BT raw data [' + str(int(100 * np.round(x / len(D), 2))) + '%], plotting connections...',
          end='')
    for y in range(x):
        if x == y or adjacent_matrix[x][y] != 1:
            continue
        # print(adjacent_matrix[x][y])
        eastings = [D[str(x)]['E'],D[str(y)]['E']]
        northings = [D[str(x)]['N'],D[str(y)]['N']]
        res_list_en = convert_lonlat(eastings, northings)
        x_lon = res_list_en[0][0]
        x_lat = res_list_en[1][0]
        y_lon = res_list_en[0][1]
        y_lat = res_list_en[1][1]
        plt.plot([y_lon, x_lon], [y_lat, x_lat], color='gray', linewidth=0.08, transform=ccrs.PlateCarree(), alpha=0.8,
                 zorder=2)


    eastings = [D[str(x)]['E']]
    northings = [D[str(x)]['N']]
    res_list_en = convert_lonlat(eastings, northings)
    x_lon = res_list_en[0][0]
    x_lat = res_list_en[1][0]
    x_lon_list += [res_list_en[0][0]]
    x_lat_list += [res_list_en[1][0]]
    if x in Level_dict['tier_1']:
        x_tier1_lon_list += [res_list_en[0][0]]
        x_tier1_lat_list += [res_list_en[1][0]]
    elif x in Level_dict['inner core']:
        x_ic_lon_list += [res_list_en[0][0]]
        x_ic_lat_list += [res_list_en[1][0]]
    elif x in Level_dict['metro']:
        x_metro_lon_list += [res_list_en[0][0]]
        x_metro_lat_list += [res_list_en[1][0]]
    elif x in Level_dict['outer core']:
        x_oc_lon_list += [res_list_en[0][0]]
        x_oc_lat_list += [res_list_en[1][0]]
    else:
        print('error')

        # time.sleep(0.00001)


        # plt.plot([y_lon,x_lon], [y_lat, x_lat],  color='gray',linewidth =0.08, marker='.',  markerfacecolor='lightskyblue', ms=3, markeredgecolor='black', markeredgewidth=0.2, transform=ccrs.PlateCarree(),alpha=0.8 )
# plt.scatter(x_lon_list, x_lat_list, color='palevioletred', marker='.', s = 6, linewidths=0.1, edgecolors='black', transform=ccrs.PlateCarree(), zorder=2 )
plt.scatter(x_tier1_lon_list, x_tier1_lat_list, color='palevioletred', marker='.', s = 6, linewidths=0.1, edgecolors='black', transform=ccrs.PlateCarree(),  zorder=2, label='Tier 1')
plt.scatter(x_metro_lon_list, x_metro_lat_list, color='lightskyblue', marker='.', s = 6, linewidths=0.1, edgecolors='black', transform=ccrs.PlateCarree(), zorder=3, label='Metro' )
plt.scatter(x_oc_lon_list, x_oc_lat_list, color='lightskyblue', marker='.', s = 6, linewidths=0.1, edgecolors='black', transform=ccrs.PlateCarree(), zorder=4 , label='Outer Core')
plt.scatter(x_ic_lon_list, x_ic_lat_list, color='mediumseagreen', marker='.', s = 6, linewidths=0.1, edgecolors='black', transform=ccrs.PlateCarree(), zorder=5 , label='Inner Core')


# Create a feature for States/Admin 1 regions at 1:50m from Natural Earth
# states_provinces = cfeature.NaturalEarthFeature(
#     category='cultural',
#     name='admin_1_states_provinces_lines',
#     scale='50m',
#     facecolor='none')

SOURCE = 'Natural Earth'
LICENSE = 'public domain'

states = cfeature.NaturalEarthFeature('cultural', 'admin_1_states_provinces', '10m', edgecolor='gray',facecolor='none')
ax.add_feature(states, linewidth = 0.1, linestyle='-')
ax.add_feature(cfeature.LAND)
# ax.add_feature(cfeature.COASTLINE)
# ax.add_feature(states_provinces, edgecolor='gray')

# Add a text annotation for the license information to the
# the bottom right corner.
text = AnchoredText('\u00A9 {}; license: {}'
                    ''.format(SOURCE, LICENSE),
                    loc=4, prop={'size': 5}, frameon=True)
ax.add_artist(text)
plt.legend(loc = "upper right", ncol=1, fontsize=5)
print(' Done')
plt.savefig('../figures/BT-UK-topo-nouk.png',dpi=600,format='png', bbox_inches='tight')
# plt.savefig('../figures/BT-UK-topo.pdf',dpi=600,format='pdf', bbox_inches='tight')

plt.show()

