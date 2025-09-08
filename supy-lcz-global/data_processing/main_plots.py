import pandas as pd
import os
import numpy as np
import xarray as xr
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, ScalarFormatter, PercentFormatter, MultipleLocator
from matplotlib.ticker import FixedLocator, FixedFormatter
from matplotlib.ticker import AutoLocator, MaxNLocator

import matplotlib.ticker
os.chdir(r"C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global")
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

SMALL_SIZE = 6
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

###########
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

# Testing
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

# monsooonal averages and basic arithmetics

ds_uf = ds_unflattened

uhi = ds_uf['T2'] - ds_uf_ff['T2']
uhi_nan = uhi.where(uhi >= 0, np.nan)
uhi_clean = uhi.where(uhi >= 0, 0)

uhi_mean = uhi_clean.mean(dim = "timestamp", keep_attrs = True)

temp_ne = xr.concat([ds_uf['T2'].sel(timestamp=ne_monsoon1), ds_uf['T2'].sel(timestamp=ne_monsoon2)], dim = 'timestamp')
temp_ne_mean = temp_ne.mean(dim = "timestamp", keep_attrs = True)

temp_sw = ds_uf['T2'].sel(timestamp=sw_monsoon)
temp_sw_mean = temp_sw.mean(dim = "timestamp", keep_attrs = True)

temp_trans = xr.concat([ds_uf['T2'].sel(timestamp=trans_monsoon1), ds_uf['T2'].sel(timestamp=trans_monsoon2)], dim = 'timestamp')
temp_trans_mean = temp_trans.mean(dim = "timestamp", keep_attrs = True)

uhi_ne = xr.concat([uhi.sel(timestamp=ne_monsoon1), uhi.sel(timestamp=ne_monsoon2)], dim = 'timestamp')
uhi_ne_mean = uhi_ne.mean(dim = "timestamp", keep_attrs = True)

uhi_sw = uhi.sel(timestamp=sw_monsoon)
uhi_sw_mean = uhi_sw.mean(dim = "timestamp", keep_attrs = True)

uhi_trans = xr.concat([uhi.sel(timestamp=trans_monsoon1), uhi.sel(timestamp=trans_monsoon2)], dim = 'timestamp')
uhi_trans_mean = uhi_trans.mean(dim = "timestamp", keep_attrs = True)


#%%

# Line graphs of average hourly tempearture/UHI
   
temp_ne_hour = temp_ne.groupby("timestamp.hour").mean()
temp_ne_hour_mean = temp_ne_hour.mean(dim = ["y","x"], keep_attrs = True)
# plt.plot(temp_ne_hour_mean)

temp_sw_hour = temp_sw.groupby("timestamp.hour").mean()
temp_sw_hour_mean = temp_sw_hour.mean(dim = ["y","x"], keep_attrs = True)
# plt.plot(temp_hour_mean_sw)

temp_uhi_hour = uhi.groupby("timestamp.hour").mean()
temp_uhi_hour_mean = temp_uhi_hour.mean(dim = ["y", "x"]) 
# plt.plot(temp_uhi_hour_mean)

uhi_hour_ne = uhi_ne.groupby("timestamp.hour").mean()
uhi_nan = uhi.where(uhi >= 0, np.nan)
uhi_hour_ne_mean = uhi_hour_ne.mean(dim = ["y", "x"]) 

uhi_hour_sw = uhi_sw.groupby("timestamp.hour").mean()
uhi_hour_sw_mean = uhi_hour_sw.mean(dim = ["y", "x"]) 

fig, ax1 = plt.subplots(dpi = 200)

ax1.plot(uhi_hour_ne_mean, "blue")
ax1.plot(uhi_hour_sw_mean, "green")
ax1.set_xlabel("Hour of Day")
ax1.set_ylabel("Temperature at 2m [deg C]")

ax2 = ax1.twinx()
ax2.set_ylabel("Difference in Temperature")
ax2.plot(temp_ne_hour_mean - temp_sw_hour_mean, "red")

fig.legend(["NE Monsoon", "SW Monsoon", "Temperature Delta"])


#%%

from whittaker_eilers import WhittakerSmoother
import seaborn as sns
# line graph showing average UHI per day over the course of the year

temp_uhi_day = uhi.resample(timestamp='D').mean()
# temp_uhi_day = temp_uhi_day.mean(dim = ["y", "x"]) 
# plt.plot(temp_uhi_day)

# ignore grids with daily UHI magnitude less than 0
temp_uhi_day_clean = temp_uhi_day.where(temp_uhi_day >= 0, np.nan)

temp_uhi_day_clean = temp_uhi_day_clean.mean(dim = ["y", "x"]) 
temp_uhi_day_clean = temp_uhi_day_clean[:-1]

whittaker_smoother = WhittakerSmoother(
    lmbda=100, order=6, data_length=len(temp_uhi_day_clean)
)


smoothed_temp = whittaker_smoother.smooth(temp_uhi_day_clean)

results = whittaker_smoother.smooth_optimal(temp_uhi_day_clean, break_serial_correlation=True)
optimally_smoothed_series = results.get_optimal().get_smoothed()

results.get_optimal().get_lambda() #lambda used 

plt.plot(temp_uhi_day_clean)
plt.plot(smoothed_temp, color='red')
plt.plot(optimally_smoothed_series, color='green')

plt.show()

uhi_df = temp_uhi_day_clean.to_dataframe()
uhi_smooth = pd.Series(optimally_smoothed_series, uhi_df.index, name = "smooth")


uhi_df = pd.concat([uhi_df, uhi_smooth], axis = 1, join = 'outer')

uhi_dfm = df.melt('tiemstamp', y="vals", hue='cols')

seaborn_grid = sns.relplot(y= x = 'timestamp', data=uhi_df, kind="line")
seaborn_grid = sns.relplot(data=optimally_smoothed_series, kind="line")

#%% Monsoonal Maps and UHI

fig, axs = plt.subplots(2, 3, figsize=(6.27,4), dpi = 300)
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

# 2nd row
contour1 = axs[1, 0].contourf(lat, lon, uhi_ne_mean, cmap = 'YlOrRd', vmin = 0, vmax = 5)
contour2 = axs[1, 1].contourf(lat, lon, uhi_sw_mean, cmap = 'YlOrRd', vmin = 0, vmax = 5)
contour3 = axs[1, 2].contourf(lat, lon, uhi_trans_mean, cmap = 'YlOrRd', vmin = 0, vmax = 5)

# Create separate colorbar axes for each row
cbar_ax1 = fig.add_axes([0.88, 0.52, 0.02, 0.35])
cbar_ax2 = fig.add_axes([0.88, 0.12, 0.02, 0.35])

# Add colorbars
cb1 = fig.colorbar(pcm1, cax=cbar_ax1)
cb1.set_label(label='Mean Temperature [deg C]', size=8)
cb1.ax.tick_params(labelsize=7, width = 0.5) 

cb2 = fig.colorbar(contour1, cax=cbar_ax2)
cb2.set_label(label='Urban Heat Island [deg C]', size=8)
cb2.ax.tick_params(labelsize=7, width = 0.5) 

for ax in axs[:, 0]:
    ax.yaxis.set_major_formatter(y_label)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=8))

for ax in axs[1, :]:
    ax.tick_params(width = 0.5)
    ax.xaxis.set_major_formatter(x_label)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6))

for ax in axs[0, :]:
    ax.tick_params(bottom=False, width = 0.5)
    ax.set_xticklabels([])
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6)) 
    
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

#%% summary stratistics

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

# histogram
plt.hist(filtered_uhi_ne.values.flatten(), bins=30, color='skyblue', edgecolor='black')
plt.xlabel('Values')
plt.ylabel('Frequency')
plt.title('Basic Histogram')
plt.show()


# annual means, iqr, mean testing, deciles?

# .mean() .median()

# count, number of grids with avg UHI > 1, 2, 3, 4

