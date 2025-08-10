# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 02:51:40 2025

@author: Danish
"""

import pandas as pd
import os
import numpy as np
import xarray as xr
from pathlib import Path
from pyproj import CRS
from pyproj import Transformer
import geopandas as gpd
import matplotlib.pyplot as plt

os.chdir(r"C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global")
# os.chdir('/home/zcfaada@ad.ucl.ac.uk/Documents/UrbClimUGdissert/supy-lcz-global')
# use the same names as set in run_split_models

data_raw = r"C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global\data\GreaterKL-2017_Y1_M2sp_3sf_R1_s1\output\grid\df_output_uMF_uLCu.h5"
split_df = pd.read_hdf(data_raw)
print(split_df)

variable_list = ['Kdown', 'Kup', 'Ldown', 'Lup', 'Tsurf', 'QN', 'QF', 'QS', 'QH', 'QE', 'QHlumps', 'QElumps', 'QHresis', 'AlbBulk', 'Ts', 'T2', 'Q2', 'U10', 'RH2']
split_metre_length =  1000
split_grid_length = 5
split_site_lat = 2.916310813222783
split_site_lon = 101.4772053501332

crs_dict = {
        'proj': 'utm',
        'zone': int(np.round((183 + split_site_lat) / 6)),
        'south': split_site_lon < 0,
    }
crs = CRS.from_dict(crs_dict)
to_utm = Transformer.from_crs(crs_from='EPSG:4326', crs_to=crs)

split_midpoint_x, split_midpoint_y = to_utm.transform(xx=split_site_lat, yy=split_site_lon)

# identify site boundaries
grid_y_max = split_midpoint_y + (split_metre_length / 2)
grid_y_min = grid_y_max - (split_metre_length)
grid_x_max = split_midpoint_x + (split_metre_length / 2)
grid_x_min = grid_x_max - (split_metre_length)

# +1 to account for the additional sample at the start, [1:] to remove before meshing.
grid_midpoint_x = np.linspace(grid_x_min, grid_x_max, split_grid_length + 1, endpoint = False)[1:]
grid_midpoint_y = np.linspace(grid_y_min, grid_y_max, split_grid_length + 1, endpoint = False)[1:]

# converting back to latlong
from_utm = Transformer.from_crs(crs_from=crs, crs_to='EPSG:4326')
grid_midpoint_lat, grid_midpoint_lon = from_utm.transform(xx=grid_midpoint_x, yy=grid_midpoint_y)

# flip coords to start from bottomleft
#grid_midpoint_lat = np.flip(grid_midpoint_lat)
#grid_midpoint_lon = np.flip(grid_midpoint_lon)

# repeat latlong to form a 2d grid
split_grid_yy, split_grid_xx = np.meshgrid(grid_midpoint_lat, grid_midpoint_lon)

split_grid_lat = list(np.ndarray.flatten(split_grid_yy))
split_grid_lon = list(np.ndarray.flatten(split_grid_xx))

split_df.index.rename(['grid', 'timestamp'], inplace = True)
split_df.index = split_df.index.set_levels(split_df.index.levels[0].astype('int64'), level=0)
split_df.index = split_df.index.set_levels(split_df.index.levels[1].astype('datetime64[ns]'), level=1)

ds = xr.Dataset.from_dataframe(split_df)

ds = ds.assign_coords(latitude = ('grid', split_grid_lat))
ds = ds.assign_coords(longitude = ('grid', split_grid_lon))
print(ds)
print(ds.T2.isel(timestamp=0))

ds_sort = ds.sortby(['longitude', 'latitude'])

nlat, nlon = split_grid_length, split_grid_length

data_vars = {}
flat_data = ds['T2'].values
print(flat_data.shape)
data_reshaped = flat_data.reshape(nlat, nlon, -1)
print(data_reshaped.shape)
data_vars['T2'] = (("lat", "lon", 'timestamp'), data_reshaped)


# =============================================================================
# data_vars = {}
# for var_label in variable_list:
#         flat_data = ds[var_label].values #need to instead obtain data directly from dataset 
#         data_reshaped = flat_data.reshape(-1, nlat, nlon)
#         data_vars[var_label] = (("timestamp","lat", "lon"), data_reshaped)
# =============================================================================
        
unflattened_ds = xr.Dataset(data_vars,
                                  coords = {
        'timestamp': ds['timestamp'],
        'latitude': (('lat', 'lon'), split_grid_yy),
        'longitude': (('lat', 'lon'), split_grid_xx)})

unflattened_ds.T2.isel(timestamp=8).plot.pcolormesh()
print(unflattened_ds.T2.isel(timestamp=16))







