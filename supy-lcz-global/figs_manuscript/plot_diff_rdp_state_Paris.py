import pandas as pd
import xarray as xr
import rioxarray as rxr
import os
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from rasterio.warp import reproject
from rasterio.warp import Resampling

# For the fractions

# SUEWS tate file + RDP file
fn_state = "/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/output/grid/df_state_3_2b_fractions_raster.nc"
fn_rdp = "/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/input/grid/rdp_fractions.nc"

ds_state = xr.open_dataset(fn_state)
ds_state = ds_state.rename({'x': 'lon','y': 'lat'})
ds_rdp = xr.open_dataset(fn_rdp)
ds_rdp = ds_rdp.rename({'Lon': 'lon','Lat': 'lat'})

regridder = xe.Regridder(ds_rdp, ds_state, 'bilinear')
ds_rdp_2_state = regridder(ds_rdp)

OFILE = "/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/output/grid/rdp_fractions_state_raster.nc"
ds_rdp_2_state.to_netcdf(OFILE)


# For the Building properties
fn_state = "/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/output/grid/df_state_3_2b_fractions_raster.nc"
fn_rdp = "/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/input/grid/rdp_other.nc"

ds_state = xr.open_dataset(fn_state)
ds_state = ds_state.rename({'x': 'lon','y': 'lat'})
ds_rdp = xr.open_dataset(fn_rdp)
ds_rdp = ds_rdp.rename({'Lon': 'lon','Lat': 'lat'})

regridder = xe.Regridder(ds_rdp, ds_state, 'bilinear')
ds_rdp_2_state = regridder(ds_rdp)

OFILE = "/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/output/grid/rdp_other_state_raster.nc"
ds_rdp_2_state.to_netcdf(OFILE)


# # From W2W - FAILS??
# # Info: https://rasterio.readthedocs.io/en/latest/api/rasterio.warp.html?highlight=reproject(#rasterio.warp.reproject
# ds_state.rio.write_crs(4326, inplace=True)
# ds_state.rio.write_transform(inplace=True)
#
# ds_rdp.rio.write_crs(4326, inplace=True)
# ds_rdp.rio.write_transform(inplace=True)
#
# rdp_2_state = reproject(
#     ds_rdp.BUILDING_FRACTION,
#     ds_state.Buildings,
#     src_transform=ds_rdp.rio.transform(),
#     src_crs=ds_rdp.rio.crs,
#     dst_transform=ds_state.rio.transform(),
#     dst_crs=ds_state.rio.crs,
#     resampling=Resampling['average'],
# )[0]



# From WUDAPT-to-COSMO, does not work??
# interp_object = RegularGridInterpolator(
#     (ds_rdp.Lat.data, ds_rdp.Lon.data),
#     ds_rdp['BUILDING_FRACTION'].data,
#     method="linear"
# )
#
# targetPoints = ds_state.y.data, ds_state.x.data
# rdp_resampled = interp_object(targetPoints)