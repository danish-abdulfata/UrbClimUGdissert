import pandas as pd
import os
import numpy as np
import xarray as xr
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt

os.chdir(r"C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global")
#os.chdir('/home/zcfaada@ad.ucl.ac.uk/Documents/UrbClimUGdissert/supy-lcz-global')
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

# checking if meshgrid is intact

lat_val = ds_unflattened.coords['latitude']
lon_val = ds_unflattened.coords['longitude']
print(lat_val, lon_val)

fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(14, 4))
ds_unflattened.longitude.plot(ax=ax1)
ds_unflattened.latitude.plot(ax=ax2)


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

lat_arr = ds.coords["latitude"].values
lon_arr = ds.coords["longitude"].values

lat_axes = np.linspace(min(lat_arr), max(lat_arr), 8)
lon_arr = np.linspace(min(lon_arr), max(lon_arr), 40)


temp = ds_unflattened['T2'].sel(timestamp="2017-01-01T14:00:00")
lat = ds_unflattened['x']
lon = ds_unflattened['y']

plt.figure(figsize=(10, 6))
plt.pcolormesh(lon, lat, temp, shading='auto', cmap='coolwarm')
plt.colorbar(label='Temperature at 2m [deg C]')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Temperature at 2017-01-01T14:00:00')
plt.show()


temp = ds_unflattened['T2']
temp_mean = temp.mean(dim = "timestamp", keep_attrs = True)
lat = temp_mean['x']
lon = temp_mean['y']

main = plt.figure(figsize=(10, 6))
plt.pcolormesh(lon, lat, temp_mean, shading='auto', cmap='coolwarm')
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
# for monsoon in monsoon_periods:
    








