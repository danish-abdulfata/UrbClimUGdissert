import pandas as pd
import os
import numpy as np
import xarray as xr
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, ScalarFormatter, PercentFormatter, MultipleLocator
from matplotlib.ticker import FixedLocator, FixedFormatter
from matplotlib.ticker import AutoLocator, MaxNLocator, LinearLocator, LogLocator, MultipleLocator

import matplotlib.ticker
#os.chdir(r"C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global")
os.chdir('/home/zcfaada@ad.ucl.ac.uk/Documents/UrbClimUGdissert/supy-lcz-global')
# use the same names as set in run_split_models

site_prefix = "GreaterKL-2017_Y1_M2sp_3sf_R1"


output_file = './data/consolidated_outputs/'
data_file = Path(output_file, site_prefix + '_consolidated.nc')
data_file_uf = Path(output_file, site_prefix + '_unflattened.nc')
data_surffrac = Path(output_file, site_prefix + 'surffrac_consolidated.csv')

ds = xr.open_dataset(data_file)
ds_unflattened = xr.open_dataset(data_file_uf)

model_year = slice("2017-01-01T00:00:00", "2018-01-01T00:00:00")
ds = ds.sel(timestamp=model_year)
ds_unflattened = ds_unflattened.sel(timestamp=model_year)

########## Time Periods concerned

# Northeast Monsoon
ne_monsoon1 = slice("2017-01-01T00:00:00", "2017-03-31T23:00:00")
# Monsoon Transitional Period
trans_monsoon1 =  slice("2017-04-01T00:00:00", "2017-05-16T23:00:00")
# Southwest Monsoon
sw_monsoon = slice("2017-05-17T00:00:00", "2017-09-05T23:00:00")
# Monsoon Transitional Period
trans_monsoon2 =  slice("2017-09-06T00:00:00", "2017-11-13T23:00:00")
# Northeast Monsoon
ne_monsoon2 = slice("2017-11-13T00:00:00", "2018-01-01T00:00:00")

monsoon_periods = [ne_monsoon1, trans_monsoon1, sw_monsoon, trans_monsoon1, ne_monsoon2]

###########
#%%

# checking if meshgrid is intact

lat_val = ds_unflattened.coords['latitude']
lon_val = ds_unflattened.coords['longitude']
print(lat_val, lon_val)

fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(14, 4))
ds_unflattened.longitude.plot(ax=ax1)
ds_unflattened.latitude.plot(ax=ax2)



# basic plot using state-based api

temp = ds_unflattened['T2'].sel(timestamp="2017-01-01T14:00:00")
lat = ds_unflattened['y']
lon = ds_unflattened['x']

plt.figure(figsize=(10, 6))
plt.pcolormesh(lat, lon, temp, shading='auto', cmap='coolwarm')
plt.colorbar(label='Temperature at 2m [deg C]')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Temperature at 2017-01-01T14:00:00')
plt.show()

# axes ticks and labels testing

lat_arr = ds.coords["latitude"].values
lon_arr = ds.coords["longitude"].values

lat_axes = np.linspace(min(lat_arr), max(lat_arr), 40)
lon_axes = np.linspace(min(lon_arr), max(lon_arr), 40)

def x_label(x, pos):
    if x == 40:
        return " "
    return '{:.2f}'.format(round(lon_axes[int(x)], 2))

def y_label(x, pos):
    if x == 40:
        return " "
    return '{:.2f}'.format(round(lat_axes[int(x)], 2))
    
temp = ds_unflattened['T2'].sel(timestamp="2017-01-01T14:00:00")
lat = ds_unflattened['y']
lon = ds_unflattened['x']

fig, ax1 = plt.subplots(figsize=(10,6), dpi = 200)

ax1.set_xlabel('Longitude')
ax1.set_ylabel('Latitude')
pcm = ax1.pcolormesh(lat, lon, temp, shading = 'auto', cmap='coolwarm')
# ax1.xaxis.set_major_locator(MaxNLocator(nbins=5))
ax1.set_title("Axes Label testing")
ax1.xaxis.set_major_formatter(x_label)
ax1.yaxis.set_major_formatter(y_label)

fig.colorbar(pcm, ax=ax1, label='Temperature at 2m [deg C]')
plt.show()



###########

temp = ds_unflattened['T2']
temp_mean = temp.mean(dim = "timestamp", keep_attrs = True)
lat = temp_mean['y']
lon = temp_mean['x']

main = plt.figure(figsize=(10, 6))
plt.pcolormesh(lat, lon, temp_mean, shading='auto', cmap='coolwarm')
plt.colorbar(label='Temperature at 2m [deg C]')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Average Temperature in 2017')
main.set_yticks(lat_axes)
plt.show()

ds_day = ds_unflattened.groupby("timestamp.day").max()
ds_day_sum = (ds_day["T2"]>= 35).sum(dim="day")
lat = ds_day_sum['x']
lon = ds_day_sum['y']

main = plt.figure(figsize=(10, 6))
plt.pcolormesh(lon, lat, ds_day_sum, shading='auto', cmap='Reds')
plt.colorbar(label='Number of days')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Number of days above 35 deg C in 2017')
plt.show()

hour_mean = ds_unflattened.isel(timestamp=(ds.timestamp.dt.hour == 14))
hour_mean = hour_mean["RH2"].mean(dim = "timestamp")
lat = hour_mean['x']
lon = hour_mean['y']

main = plt.figure(figsize=(10, 6))
plt.pcolormesh(lon, lat, hour_mean, shading='auto', cmap='Blues')
plt.colorbar(label='Relative Humidity [%]')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Average humidity at 14:00')
plt.show()

ds.resample(time="1D")

#%% 

# stuff to figure out
    # fix formatting problems, figure out way to deal with axes

fig, axs = plt.subplots(3, 4, figsize=(15,10), dpi = 200, gridspec_kw={'width_ratios': [0.6, 0.6, 0.25, 0.6]})
fig.subplots_adjust(hspace = 0.05, wspace = 0.03, right = 0.87)

for ax in axs[:, 2]: 
    ax.axis("off") 

temp_ne = ds_unflattened['T2'].sel(timestamp=ne_monsoon2)
temp_mean_ne = temp_ne.mean(dim = "timestamp", keep_attrs = True)

temp = ds_unflattened['T2'].sel(timestamp=ne_monsoon1)
temp_mean = temp.mean(dim = "timestamp", keep_attrs = True)
lat = temp_mean['y']
lon = temp_mean['x']

axs[0, 0].set_title("Northeast Monsoon")
axs[0, 1].set_title("Southwest Monsoon")
axs[0, 3].set_title("Difference")

pcm1 = axs[0, 0].pcolormesh(lat, lon, (temp_mean + temp_mean_ne)/2, shading = 'auto', cmap='coolwarm', vmin = 24, vmax = 32)

temp2 = ds_unflattened['T2'].sel(timestamp=sw_monsoon)
temp_mean2 = temp2.mean(dim = "timestamp", keep_attrs = True)

pcm2 = axs[0, 1].pcolormesh(lat, lon, temp_mean2, shading = 'auto', cmap='coolwarm', vmin = 24, vmax = 32)

contour1 = axs[0, 3].contourf(lat, lon, (temp_mean + temp_mean_ne)/2 - temp_mean2, vmin = -1.8, vmax = -0.4)


# 09:00 average tempearture

temp_trans1 = ds_unflattened['T2'].sel(timestamp=trans_monsoon1)
temp_mean3 = temp_trans1.mean(dim = "timestamp", keep_attrs = True)
pcm4 = axs[1, 0].pcolormesh(lat, lon, temp_mean3, shading = 'auto', cmap='coolwarm', vmin = 24, vmax = 32)

contour2 = axs[1, 3].contourf(lat, lon, (temp_mean + temp_mean_ne)/2 - temp_mean3, vmin = -1.8, vmax = -0.4)


# 20:00

for ax in axs[:, 0]:
    ax.yaxis.set_major_formatter(y_label)

for ax in axs[2, :]:
    ax.xaxis.set_major_formatter(x_label)
    
for ax in axs[0, :]:
    ax.set_xticklabels([])
for ax in axs[1, :]:
    ax.set_xticklabels([])  
    
for ax in axs[:, 1]:
    ax.set_yticklabels([])
for ax in axs[:, 3]:
    ax.set_yticklabels([])  
    
# for ax in axs[2]:
#     ax.set_yticklabels([])
#     ax.set_xticklabels([])
        # ax.yaxis.set_visible(False)
        # ax.xaxis.set_visible(False)


cbar_tdiff = fig.add_axes([0.88, 0.15, 0.02, 0.7])
fig.colorbar(contour1, cax = cbar_tdiff, label='Temperature difference [deg C]')

cbar_ax = fig.add_axes([0.58, 0.15, 0.02, 0.7])
fig.colorbar(pcm1, cax=cbar_ax, label='Temperature at 2m [deg C]')


plt.show()
    
#%%

# Line graphs of average tempearture at a certain time?
    # average temperature throughout the day for each season. 
    # specific grids or generally?

# use a differnet package for this?
# maybe plotnine
   
temp_ne1 = ds_unflattened['T2'].sel(timestamp=ne_monsoon1)
temp_ne2 = ds_unflattened['T2'].sel(timestamp=ne_monsoon2)

temp_hour_mean_ne1 = temp_ne1.groupby("timestamp.hour").mean()
temp_hour_mean_ne1 = temp_hour_mean_ne1.mean(dim = ["y","x"], keep_attrs = True)
temp_hour_mean_ne2 = temp_ne1.groupby("timestamp.hour").mean()
temp_hour_mean_ne2 = temp_hour_mean_ne2.mean(dim = ["y","x"], keep_attrs = True)

temp_hour_mean_ne = (temp_hour_mean_ne1 + temp_hour_mean_ne2)/2

# plt.plot(temp_hour_mean_ne)

temp_sw = ds_unflattened['T2'].sel(timestamp=sw_monsoon)
temp_hour_mean_sw = temp_sw.groupby("timestamp.hour").mean()
temp_hour_mean_sw = temp_hour_mean_sw.mean(dim = ["y","x"], keep_attrs = True)
# plt.plot(temp_hour_mean_sw)

fig, ax1 = plt.subplots(dpi = 200)

ax1.plot(temp_hour_mean_ne, "blue")
ax1.plot(temp_hour_mean_sw, "green")
ax1.set_xlabel("Hour of Day")
ax1.set_ylabel("Temperature at 2m [deg C]")

ax2 = ax1.twinx()
ax2.set_ylabel("Difference in Temperature")
ax2.plot(temp_hour_mean_ne - temp_hour_mean_sw, "red")

fig.legend(["NE Monsoon", "SW Monsoon", "Temperature Delta"])



