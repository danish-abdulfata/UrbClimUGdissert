# -*- coding: utf-8 -*-
import pandas as pd
import os
import numpy as np
import xarray as xr
from pathlib import Path
import scipy.stats as stats
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FixedLocator
from matplotlib.lines import Line2D

os.chdir(r"C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global")
#os.chdir(r"C:\Users\ahmad\Documents\UrbClimUGdissert\supy-lcz-global")
#os.chdir('/home/zcfaada@ad.ucl.ac.uk/Documents/UrbClimUGdissert/supy-lcz-global')

# use the same names as set in run_split_models

site_prefix = "GreaterKL-2017_Y1_M2sp_3sf_R1"


output_file = './data/consolidated_outputs/'
data_file = Path(output_file, site_prefix + '_consolidated.nc')
data_file_uf = Path(output_file, site_prefix + '_unflattened.nc')
data_surffrac = Path(output_file, site_prefix + 'surffrac_consolidated.csv')

data_file_h5 = Path(output_file, site_prefix + '_consolidated.h5')
df = pd.read_hdf(data_file_h5)

ds = xr.open_dataset(data_file)
ds_unflattened = xr.open_dataset(data_file_uf)

ds_uf_ff = Path(output_file, "GreaterKL-2017_Y1_M2sp_3sf_R2_unflattened.nc")
ds_uf_ff = xr.open_dataset(ds_uf_ff)

model_year = slice("2017-01-01T00:00:00", "2018-01-01T00:00:00")
ds = ds.sel(timestamp=model_year)
ds_unflattened = ds_unflattened.sel(timestamp=model_year)
ds_uf = ds_unflattened

ds_uf_ff = ds_uf_ff.sel(timestamp=model_year)

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


# Font sizes and family

SMALL_SIZE = 8
MEDIUM_SIZE = 10
BIGGER_SIZE = 12

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

plt.rcParams["font.family"] = "TeX Gyre Termes"

# monsooonal averages and basic arithmetics

uhi = ds_uf['T2'] - ds_uf_ff['T2']
uhi_nan = uhi.where(uhi >= 0, np.nan)
uhi_clean = uhi.where(uhi >= 0, 0)

uhi_mean = uhi_clean.mean(dim = "timestamp", keep_attrs = True)

nem = xr.concat([ds_uf.sel(timestamp=ne_monsoon1), ds_uf.sel(timestamp=ne_monsoon2)], dim = 'timestamp')
temp_ne_mean = nem['T2'].mean(dim = "timestamp", keep_attrs = True)

swm = ds_uf.sel(timestamp=sw_monsoon)
temp_sw_mean = swm['T2'].mean(dim = "timestamp", keep_attrs = True)

tmp = xr.concat([ds_uf.sel(timestamp=trans_monsoon1), ds_uf.sel(timestamp=trans_monsoon2)], dim = 'timestamp')
temp_trans_mean = tmp['T2'].mean(dim = "timestamp", keep_attrs = True)

uhi_ne = xr.concat([uhi.sel(timestamp=ne_monsoon1), uhi.sel(timestamp=ne_monsoon2)], dim = 'timestamp')
uhi_ne_mean = uhi_ne.mean(dim = "timestamp", keep_attrs = True)

uhi_sw = uhi.sel(timestamp=sw_monsoon)
uhi_sw_mean = uhi_sw.mean(dim = "timestamp", keep_attrs = True)

uhi_trans = xr.concat([uhi.sel(timestamp=trans_monsoon1), uhi.sel(timestamp=trans_monsoon2)], dim = 'timestamp')
uhi_trans_mean = uhi_trans.mean(dim = "timestamp", keep_attrs = True)

###########

# axes ticks and labels preparation

lat_arr = ds.coords["latitude"].values
lon_arr = ds.coords["longitude"].values

lat_axes = np.linspace(min(lat_arr), max(lat_arr), 40)
lon_axes = np.linspace(min(lon_arr), max(lon_arr), 40)


def x_label(x, pos):
    if x == 40:
        return " "
    return '{:.2f}'.format(round(lon_axes[int(x)], 3))

def y_label(x, pos):
    if x == 40:
        return " "
    return '{:.2f}'.format(round(lat_axes[int(x)], 3))

x_tick_indices = [4, 14, 24, 34]
y_tick_indices = [4, 12, 20, 28, 36]

#%%

# checking if meshgrid is intact

lat_val = ds_unflattened.coords['latitude']
lon_val = ds_unflattened.coords['longitude']
print(lat_val, lon_val)

fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(14, 4))
ds_unflattened.longitude.plot(ax=ax1)
ds_unflattened.latitude.plot(ax=ax2)


# basic header display

print(ds_unflattened.coords['latitude'].head())
print(ds_unflattened.coords['longitude'].head())

print(ds_unflattened.timestamp.values[:1])
print(ds_unflattened.longitude.values[38])
print(ds_unflattened.latitude.values[38])

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
    
#%%
# axes ticks and labels example

temp = ds_unflattened['T2'].sel(timestamp="2017-01-01T14:00:00")
lat = ds_unflattened['y']
lon = ds_unflattened['x']
fig, ax1 = plt.subplots(figsize=(6,4), dpi = 200)

ax1.set_xlabel('Longitude')
ax1.set_ylabel('Latitude')
pcm = ax1.pcolormesh(lat, lon, temp, shading = 'auto', cmap='coolwarm')
# ax1.xaxis.set_major_locator(MaxNLocator(nbins=5))
ax1.set_title("Axes Label testing")

ax1.xaxis.set_major_locator(MaxNLocator(nbins=6))
ax1.yaxis.set_major_locator(MaxNLocator(nbins=6))

ax1.xaxis.set_major_formatter(x_label)
ax1.yaxis.set_major_formatter(y_label)

fig.colorbar(pcm, ax=ax1, label='Temperature at 2m [deg C]')
plt.show()

#%%
# Basic figures and testing

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

# Testing subplots
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

temp_trans1 = ds_unflattened['T2'].sel(timestamp=trans_monsoon1)
temp_mean3 = temp_trans1.mean(dim = "timestamp", keep_attrs = True)
pcm4 = axs[1, 0].pcolormesh(lat, lon, temp_mean3, shading = 'auto', cmap='coolwarm', vmin = 24, vmax = 32)

contour2 = axs[1, 3].contourf(lat, lon, (temp_mean + temp_mean_ne)/2 - temp_mean3, vmin = -1.8, vmax = -0.4)


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

cbar_tdiff = fig.add_axes([0.88, 0.15, 0.02, 0.7])
fig.colorbar(contour1, cax = cbar_tdiff, label='Temperature difference [deg C]')

cbar_ax = fig.add_axes([0.58, 0.15, 0.02, 0.7])
fig.colorbar(pcm1, cax=cbar_ax, label='Temperature at 2m [deg C]')
plt.show()

#%%

#################################### DEFAULT local climate calculations ####################################
# first half of the data figures

# Summary and descriptive statistics

annual = ds_uf['T2'].mean(dim = ["y", "x"])
annual = annual.groupby("timestamp.day").mean()

nem_temp = nem['T2'].mean(dim = ["y", "x"])
nem_temp = nem_temp.groupby("timestamp.day").mean()

swm_temp = swm['T2'].mean(dim = ["y", "x"])
swm_temp = swm_temp.groupby("timestamp.day").mean()

tmp_temp = tmp['T2'].mean(dim = ["y", "x"])
tmp_temp = tmp_temp.groupby("timestamp.day").mean()

data = [annual, nem_temp, swm_temp, tmp_temp]

annual_rh2 = ds_uf['RH2'].mean(dim = ["y", "x"])
annual_rh2 = annual_rh2.groupby("timestamp.day").mean()

nem_rh2 = nem['RH2'].mean(dim = ["y", "x"])
nem_rh2 = nem_rh2.groupby("timestamp.day").mean()

swm_rh2 = swm['RH2'].mean(dim = ["y", "x"])
swm_rh2 = swm_rh2.groupby("timestamp.day").mean()

tmp_rh2 = tmp['RH2'].mean(dim = ["y", "x"])
tmp_rh2 = tmp_rh2.groupby("timestamp.day").mean()

data_humidity = [annual_rh2, nem_rh2, swm_rh2, tmp_rh2]

# boxplots

fig, axs = plt.subplots(1, 2, figsize=(6.27,2), dpi = 1000)
bp = axs[0].boxplot(data, showfliers=False)
fig.subplots_adjust(wspace = 0.3)

axs[0].set_ylabel('Temperature [°C]')

axs[0].set_xticklabels(['Year', 'NEM', 'SWM', 'TMP'], fontsize = 10)

bp2 = axs[1].boxplot(data_humidity, showfliers=False)

axs[1].set_ylabel('Relative humidity [%]') 
axs[1].set_xticklabels(['Year', 'NEM', 'SWM', 'TMP'], fontsize = 10)

# axs[0].tick_params(axis='y', labelsize=8)
# axs[1].tick_params(axis='y', labelsize=8)

axs[0].text(0.02, 0.97, "(a)", transform=axs[0].transAxes, 
            fontsize=12, fontweight='bold', va='top')
axs[1].text(0.02, 0.97, "(b)", transform=axs[1].transAxes, 
            fontsize=12, fontweight='bold', va='top')

plt.show()

#%%
# figure of mean annual temps and humidity

fig, axs = plt.subplots(1, 2, figsize=(6.27,2), dpi = 1000)
fig.subplots_adjust(wspace = 0.30)

ds_t2 = ds_uf["T2"].mean(dim = "timestamp")
ds_rh2 = ds_uf["RH2"].mean(dim = "timestamp")
lat = ds_uf['x']
lon = ds_uf['y']

t2 = axs[0].pcolormesh(lat, lon, ds_t2, shading = 'auto', cmap='Oranges', vmin = 24, vmax = 32)
rh2 = axs[1].pcolormesh(lat, lon, ds_rh2, shading = 'auto', cmap='Blues', vmin = 70, vmax = 90)

cb_t2 = plt.colorbar(t2)
ch_rh2 = plt.colorbar(rh2)

cb_t2.set_label(label='Mean Temperature [°C]', size=10, rotation=270, labelpad=15)
ch_rh2.set_label(label='Relative Humidity [%]', size=10, rotation=270, labelpad=15)

for ax in axs:
    ax.yaxis.set_major_formatter(y_label)
    ax.yaxis.set_major_locator(FixedLocator(y_tick_indices))

    ax.tick_params(width = 0.5)
    ax.xaxis.set_major_formatter(x_label)
    # Get current ticks and start from 5th position
    current_ticks = ax.get_xticks()
    ax.xaxis.set_major_locator(FixedLocator(x_tick_indices))

#%%
#################################### UHI calculations and figures ####################################
# second half of the data figures

# percentile based on highest annual mean temperatures in 'default'
# Hourly means linegraphs
percentiles = [0, 0.5, 0.75, 0.9]

# Calculate temporal mean for each grid cell
gridded_mean = ds_uf['T2'].mean(dim='timestamp')

# Intialize final dataframes
hour_index = range(24)

final_ne_hourly = pd.DataFrame(index = hour_index)
final_sw_hourly = pd.DataFrame(index = hour_index)
final_tmp_hourly = pd.DataFrame(index = hour_index)

# Calculate the percentile value
for percentile in percentiles:
    
    percentile_grid = gridded_mean.quantile(percentile)
    # Create boolean mask for top percentile grids
    warmest_percent = gridded_mean >= percentile_grid

    # Apply the mask to select only top percentile grids
    warmest_grids = ds_uf['T2'].where(warmest_percent, drop=True)
    warmest_grids_ff = ds_uf_ff['T2'].where(warmest_percent, drop=True)

    # UHI calculations and selection
    warmest_grids_uhi = warmest_grids - warmest_grids_ff
    warmest_grids_uhi = warmest_grids_uhi.where(warmest_grids_uhi >= 0, np.nan)

    warmest_grids_uhi_ne = xr.concat([warmest_grids_uhi.sel(timestamp=ne_monsoon1), warmest_grids_uhi.sel(timestamp=ne_monsoon2)], dim = 'timestamp')
    warmest_grids_uhi_sw = warmest_grids_uhi.sel(timestamp=sw_monsoon)
    warmest_grids_uhi_tmp = xr.concat([warmest_grids_uhi.sel(timestamp=trans_monsoon1), warmest_grids_uhi.sel(timestamp=trans_monsoon2)], dim = 'timestamp')

    # Perform calculations on the filtered data

    percentile_ne = warmest_grids_uhi_ne.mean(dim = ["y", "x"])
    percentile_sw = warmest_grids_uhi_sw.mean(dim = ["y", "x"])
    percentile_tmp = warmest_grids_uhi_tmp.mean(dim = ["y", "x"])
    percentile_ne_hourly = percentile_ne.groupby("timestamp.hour").mean()
    percentile_sw_hourly = percentile_sw.groupby("timestamp.hour").mean()
    percentile_tmp_hourly = percentile_tmp.groupby("timestamp.hour").mean()
    
    # merge to final dataframe
    
    final_ne_hourly = final_ne_hourly.merge(percentile_ne_hourly.to_pandas(), left_index = True, right_index = True, suffixes = (None, "_" + str(percentile)))
    final_sw_hourly = final_sw_hourly.merge(percentile_sw_hourly.to_pandas(), left_index = True, right_index = True, suffixes = (None, "_" + str(percentile)))
    final_tmp_hourly = final_tmp_hourly.merge(percentile_tmp_hourly.to_pandas(), left_index = True, right_index = True, suffixes = (None, "_" + str(percentile)))

#%%

# percentile based on  annual mean UHII
# Hourly means linegraphs
percentiles = [0, 0.5, 0.75, 0.9]

# Intialize final dataframes
hour_index = range(24)

final_ne_hourly = pd.DataFrame(index = hour_index)
final_sw_hourly = pd.DataFrame(index = hour_index)
final_tmp_hourly = pd.DataFrame(index = hour_index)

# Calculate the percentile value
for percentile in percentiles:
    
    # only taking into account percentile grids for highest ANNUAL UHII
    gridded_mean = uhi.mean(dim='timestamp')
    gridded_mean = gridded_mean.where(gridded_mean >= 0, np.nan)
    percentile_grid = gridded_mean.quantile(percentile)
    warmest_percent = uhi >= percentile_grid
    
    warmest_uhi = uhi.where(warmest_percent, drop=True)
    
    # filter data based on season
    warmest_uhi_ne = xr.concat([warmest_uhi.sel(timestamp=ne_monsoon1), warmest_uhi.sel(timestamp=ne_monsoon2)], dim = 'timestamp')
    warmest_uhi_sw = warmest_uhi.sel(timestamp=sw_monsoon)
    warmest_uhi_tmp = xr.concat([warmest_uhi.sel(timestamp=trans_monsoon1), warmest_uhi.sel(timestamp=trans_monsoon2)], dim = 'timestamp')

    # Perform calculations on the filtered data

    percentile_ne = warmest_uhi_ne.mean(dim = ["y", "x"])
    percentile_sw = warmest_uhi_sw.mean(dim = ["y", "x"])
    percentile_tmp = warmest_uhi_tmp.mean(dim = ["y", "x"])
    percentile_ne_hourly = percentile_ne.groupby("timestamp.hour").mean()
    percentile_sw_hourly = percentile_sw.groupby("timestamp.hour").mean()
    percentile_tmp_hourly = percentile_tmp.groupby("timestamp.hour").mean()
    
    # merge to final dataframe
    
    final_ne_hourly = final_ne_hourly.merge(percentile_ne_hourly.to_pandas(), left_index = True, right_index = True, suffixes = (None, "_" + str(percentile)))
    final_sw_hourly = final_sw_hourly.merge(percentile_sw_hourly.to_pandas(), left_index = True, right_index = True, suffixes = (None, "_" + str(percentile)))
    final_tmp_hourly = final_tmp_hourly.merge(percentile_tmp_hourly.to_pandas(), left_index = True, right_index = True, suffixes = (None, "_" + str(percentile)))

# plotting
fig, axs = plt.subplots(1, 2, figsize=(6.27,3), dpi = 1000)
fig.subplots_adjust(hspace = 0.02, wspace = 0.30)

# Add corner labels for caption reference
axs[0].text(0.89, 0.98, "(a)", transform=axs[0].transAxes, 
            fontsize=12, fontweight='bold', va='top')
axs[1].text(0.02, 0.98, "(b)", transform=axs[1].transAxes, 
            fontsize=12, fontweight='bold', va='top')

fig1 = axs[0].plot(final_ne_hourly['T2'], "lightseagreen", linestyle='-', label='NEM (All)')
fig1 = axs[0].plot(final_sw_hourly['T2'], "salmon", linestyle='-', label='SWM (All)')
# fig1 = axs[0].plot(final_tmp_hourly['T2'], "orange", linestyle='-', label='TMP (All)')

fig1 = axs[0].plot(final_ne_hourly['T2_0.5'], "lightseagreen", linestyle='--', label='NEM (Top 50%)')
fig1 = axs[0].plot(final_sw_hourly['T2_0.5'], "salmon", linestyle='--', label='SWM (Top 50%)')
# fig1 = axs[0].plot(final_tmp_hourly['T2_0.5'], "orange", linestyle='--', label='SWM (Top 50%)')

fig1 = axs[0].plot(final_ne_hourly['T2_0.75'], "lightseagreen", linestyle=':', label='NEM (Top 25%)')
fig1 = axs[0].plot(final_sw_hourly['T2_0.75'], "salmon", linestyle=':', label='SWM (Top 25%)')
# fig1 = axs[0].plot(final_tmp_hourly['T2_0.75'], "orange", linestyle=':', label='SWM (Top 25%)')

fig1 = axs[0].plot(final_ne_hourly['T2_0.9'], "lightseagreen", linestyle='-.', label='NEM (Top 10%)')
fig1 = axs[0].plot(final_sw_hourly['T2_0.9'], "salmon", linestyle='-.', label='SWM (Top 10%)')
# fig1 = axs[0].plot(final_tmp_hourly['T2_0.9'], "orange", linestyle='-.', label='SWM (Top 25%)')

label_hour = 0

# Add labels for each percentile pair
percentiles = ['T2', 'T2_0.5', 'T2_0.75', 'T2_0.9']
labels = ['All', 'Top 50%', 'Top 25%', 'Top 10%']

for i, (percentile, label) in enumerate(zip(percentiles, labels)):
    axs[0].text(label_hour, final_sw_hourly[percentile].loc[label_hour]+0.05, 
                f'{label}', va='bottom', ha='left', fontsize=7, color='black')

# (a) legend
legend_handles_a = [
    Line2D([0], [0], color='lightseagreen', lw=1, label='NEM'),
    Line2D([0], [0], color='salmon', lw=1, label='SWM'),
]

axs[0].legend(handles=legend_handles_a, loc='best', fontsize=7)

axs[0].set_xlabel("Hour")
axs[0].set_ylabel("UHII [°C]")

uhii_diff = final_sw_hourly - final_ne_hourly 

axs[1].set_prop_cycle(color=['aquamarine', 'turquoise', 'mediumturquoise', 'lightseagreen'])
fig2 = axs[1].plot(uhii_diff)
axs[1].set_xlabel("Hour")
axs[1].set_ylabel("Seasonal difference in UHII [°C]")
    
# daily mean for all
plt.axhline(y=uhii_diff['T2'].mean(), color='aquamarine', alpha = 0.25, ls = '--', label='mean')
    
stat, p = stats.wilcoxon(uhii_diff['T2'].values.flatten(), nan_policy = 'omit')

# (b) legend
diff_legend_handles = [
    Line2D([0], [0], color='aquamarine', lw=1, label='All grids'),
    Line2D([0], [0], color='turquoise', lw=1, label='Top 50%'),
    Line2D([0], [0], color='mediumturquoise', lw=1, label='Top 25%'),
    Line2D([0], [0], color='lightseagreen', lw=1, label='Top 10%'),
]

axs[1].legend(handles=diff_legend_handles, loc='best', fontsize=7)

#%%

# line graph showing average UHI per day over the course of the year
from whittaker_eilers import WhittakerSmoother

temp_uhi_day = uhi.resample(timestamp='D').mean()

#ignore grids with daily UHI magnitude less than 0
temp_uhi_day_clean = temp_uhi_day.where(temp_uhi_day >= 0, np.nan)

temp_uhi_day_clean = temp_uhi_day_clean.mean(dim = ["y", "x"]) 
temp_uhi_day_clean = temp_uhi_day_clean[:-1]

whittaker_smoother = WhittakerSmoother(
    lmbda=100, order=7, data_length=len(temp_uhi_day_clean)
)

smoothed_temp = whittaker_smoother.smooth(temp_uhi_day_clean)

results = whittaker_smoother.smooth_optimal(temp_uhi_day_clean, break_serial_correlation=True)
optimally_smoothed_series = results.get_optimal().get_smoothed()

results.get_optimal().get_lambda() #lambda used 

uhi_df = temp_uhi_day_clean.to_dataframe()
uhi_smooth = pd.Series(optimally_smoothed_series, uhi_df.index, name = "smooth")

uhi_df = pd.concat([uhi_df, uhi_smooth], axis = 1, join = 'outer')

fig, ax1 = plt.subplots(dpi = 1000)

ax1.plot(uhi_df, color= "lightseagreen", alpha=0.25)
ax1.plot(uhi_smooth, color= "lightseagreen")

ax1.axvspan('2017-04-01T00:00:00', '2017-05-16T23:00:00', color='lightgrey', alpha=0.5)
ax1.axvspan('2017-09-06T00:00:00', '2017-11-13T23:00:00', color='lightgrey', alpha=0.5)

ax1.set_xlabel("Date")
ax1.set_ylabel("Urban Heat Island Intensity [°C]")


#%% Monsoonal Maps of UHI
fig, axs = plt.subplots(2, 3, figsize=(6.27,4), dpi = 1000)
fig.subplots_adjust(hspace = 0.02, wspace = 0.02, right = 0.87)
    
axs[0, 0].set_title("NEM", fontsize=10)
axs[0, 1].set_title("SWM", fontsize=10)
axs[0, 2].set_title("TMP", fontsize=10)

lat = ds_uf['y']
lon = ds_uf['x']

# 1st row
pcm1 = axs[0, 0].pcolormesh(lat, lon, temp_ne_mean, shading = 'auto', cmap='coolwarm', vmin = 23, vmax = 31)
pcm2 = axs[0, 1].pcolormesh(lat, lon, temp_sw_mean, shading = 'auto', cmap='coolwarm', vmin = 23, vmax = 31)
pcm3 = axs[0, 2].pcolormesh(lat, lon, temp_trans_mean, shading = 'auto', cmap='coolwarm', vmin = 23, vmax = 31)

# Define custom boundaries for the colorbar
bounds = [-1.6, 0, 0.8, 1.6, 2.4, 3.2, 4.0, 4.8]  # Custom intervals

# For UHI plots (2nd row)
contour1 = axs[1, 0].contourf(lat, lon, uhi_ne_mean, levels=bounds, cmap='YlOrRd')
contour2 = axs[1, 1].contourf(lat, lon, uhi_sw_mean, levels=bounds, cmap='YlOrRd')
contour3 = axs[1, 2].contourf(lat, lon, uhi_trans_mean, levels=bounds, cmap='YlOrRd')

# Create separate colorbar axes for each row
cbar_ax1 = fig.add_axes([0.88, 0.52, 0.02, 0.35])
cbar_ax2 = fig.add_axes([0.88, 0.12, 0.02, 0.35])

# Add colorbars
cb1 = fig.colorbar(pcm1, cax=cbar_ax1)
cb1.set_label(label='Mean Temperature [°C]', size=10, rotation=270, labelpad=15)
cb1.ax.tick_params(labelsize=8, width = 0.5) 

# colorbar2 to match the custom boundaries
cb2 = fig.colorbar(contour1, cax=cbar_ax2, boundaries=bounds, ticks=bounds)
cb2.set_label(label='Urban Heat Island [°C]', size=10, rotation=270, labelpad=9)
cb2.ax.tick_params(labelsize=8, width=0.5)

x_tick_indices = [4, 14, 24, 34]
y_tick_indices = [4, 12, 20, 28, 36]

for ax in axs[:, 0]:
    ax.yaxis.set_major_formatter(y_label)
    ax.yaxis.set_major_locator(FixedLocator(y_tick_indices))

for ax in axs[1, :]:
    ax.tick_params(width = 0.5)
    ax.xaxis.set_major_formatter(x_label)
    # Get current ticks and start from 5th position
    current_ticks = ax.get_xticks()
    ax.xaxis.set_major_locator(FixedLocator(x_tick_indices))

for ax in axs[0, :]:
    ax.tick_params(bottom=False, width = 0.5)
    ax.set_xticklabels([])
    ax.xaxis.set_major_locator(FixedLocator(x_tick_indices)) 
    
for ax in axs[:, 1]:
    ax.tick_params(left=False)
    ax.set_yticklabels([])
for ax in axs[:, 2]:
    ax.tick_params(left=False)
    ax.set_yticklabels([])  
    
# for ax in axs[2]:
#     ax.set_yticklabels([])
#     ax.set_xticklabels([])
        # ax.yaxis.set_visible(False)
        # ax.xaxis.set_visible(False)

plt.show()

#%% UHI summary stratistics

from scipy.stats import wilcoxon
import scipy.stats as stats

filtered_uhi_ne = uhi_ne_mean.where(uhi_ne_mean > 1)
filtered_uhi_sw = uhi_sw_mean.where(uhi_sw_mean > 1)

w_test = filtered_uhi_ne - filtered_uhi_sw
stat, p = wilcoxon(w_test.values.flatten().round(3), nan_policy = 'omit')

print(stat, p)

# Q-Q plot
stats.probplot(filtered_uhi_ne.values.flatten(), dist="norm", plot=plt)
plt.title('Normal Q-Q plot')
plt.xlabel('Theoretical quantiles')
plt.ylabel('Ordered Values')
plt.grid(True)
plt.show()




# tables

# annual, 50%, 75%, 90%
# NEM, SWM, TMP

# 
# .mean() .median(), ,lower quartile, upper quaritile,iqr, 90 percentile,  min, max, 


#%%
# histograms

plt.hist(uhi_ne.values.flatten(), bins=100, color='skyblue', edgecolor='black')
plt.xlabel('Values')
plt.ylabel('Frequency')
plt.title('Basic Histogram')
plt.show()
# count, number of grids with daily mean UHI > 1, 2, 3?
# 
