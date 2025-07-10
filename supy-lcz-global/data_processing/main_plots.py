# -*- coding: utf-8 -*-
"""
Created on Thu Jul  3 18:37:05 2025

@author: Danish
"""

import pandas as pd
import os
import numpy as np
import xarray as xr
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt

os.chdir(r"C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global")

# use the same names as set in run_split_models

site_prefix = "GreaterKL-2017_Y1_M2sp_3sf_R1"


output_file = './data/consolidated_outputs/'
data_file = Path(output_file, site_prefix + '_consolidated.nc')
data_file_uf = Path(output_file, site_prefix + '_unflattened.nc')
data_surffrac = Path(output_file, site_prefix + 'surffrac_consolidated.csv')


ds = xr.open_dataset(data_file)
ds_unflattened = xr.open_dataset(data_file_uf)

print(ds)
print(ds_unflattened)
# =============================================================================
# temp = ds['T2'].isel(timestamp=0)
# lat = ds['latitude']
# lon = ds['longitude']
# =============================================================================

temp = ds_unflattened['T2'].isel(timestamp=0)
lat = ds_unflattened['lat']
lon = ds_unflattened['lon']

# =============================================================================
# plt.figure(figsize=(10, 6))
# plt.pcolormesh(lon, lat, temp, shading='auto', cmap='coolwarm')
# plt.colorbar(label='Temperature')
# plt.xlabel('Longitude')
# plt.ylabel('Latitude')
# plt.title('Temperature at Time 0')
# plt.show()
# 
# temp = ds_unflattened['T2'].isel(timestamp=0)
# lat = ds_unflattened['latitude']
# lon = ds_unflattened['longitude']
# =============================================================================

ds_unflattened.T2.isel(timestamp=0).plot.pcolormesh()

# checking if meshgrid is intact

lat_val = ds_unflattened.coords['latitude']
lon_val = ds_unflattened.coords['longitude']
print(lat_val, lon_val)

fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(14, 4))
ds_unflattened.longitude.plot(ax=ax1)
ds_unflattened.latitude.plot(ax=ax2)

plt.scatter(ds_unflattened.longitude.values, ds_unflattened.latitude.values, s=1)
plt.xlabel('Longitude'); plt.ylabel('Latitude')






