import pandas as pd
import os
os.environ['USE_PYGEOS'] = '0'
import xarray as xr

# output directory
o_dir = '/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/input/grid'
fn_rdp = f'{o_dir}/rdp_fractions.nc'
ds = xr.open_dataset(fn_rdp)

# There is a line around 2.44875°E and 48.93125°N that contains nans.
# This is a railway hub: https://goo.gl/maps/8hCq1K996h1Q3Y5J8
# Set to ROAD_N = 1, all others to zero
ds['BLD'] = ds['BLD'].fillna(0)
ds['ROAD'] = ds['ROAD'].fillna(1)
ds['VEGH'] = ds['VEGH'].fillna(0)
ds['VEGB'] = ds['VEGB'].fillna(0)
ds['NVEG'] = ds['NVEG'].fillna(0)
ds['WATER'] = ds['WATER'].fillna(0)

# Normalize all fields: BLD_TMP+ROAD_TMP+VEGB_TMP+NVEG_TMP+VEGH_TMP+WATER_TMP
VAR_SUM = \
    ds['ROAD'] + \
    ds['BLD'] + \
    ds['VEGH'] + \
    ds['VEGB'] + \
    ds['NVEG'] + \
    ds['WATER']

BLD_N = ds['BLD'] / VAR_SUM
ROAD_N = ds['ROAD'] / VAR_SUM
VEGH_N = ds['VEGH'] / VAR_SUM
VEGB_N = ds['VEGB'] / VAR_SUM
NVEG_N = ds['NVEG'] / VAR_SUM
WATER_N = ds['WATER'] / VAR_SUM

# Set names
BLD_N.name = 'BLD_N'
ROAD_N.name = 'ROAD_N'
VEGH_N.name = 'VEGH_N'
VEGB_N.name = 'VEGB_N'
NVEG_N.name = 'NVEG_N'
WATER_N.name = 'WATER_N'

# Add together
ds_sums = BLD_N + ROAD_N + VEGB_N + VEGH_N + NVEG_N + WATER_N
#ds_sums.plot()

# Combine into one data array
da_norm = xr.merge([BLD_N, ROAD_N, VEGH_N, VEGB_N, NVEG_N, WATER_N])

# Save as netcdf
OFILE = os.path.join(
    o_dir,
    f"rdp_fractions_norm.nc",
)
da_norm.to_netcdf(OFILE)
#
# # Check sums
# ds_sums = ds['TOWN'] + ds['NATURE'] + ds['WATER'] + ds['SEA']
# ds_sums.plot()
#
# # Check NATURE
# ds_nature = ds['VEGB'] + ds['VEGH'] + ds['NVEG']
# ds_nature = ds['VEGB'] + ds['VEGH'] + ds['NVEG']
#
# # Sum the fractions, check if 1?
# ds_sum = \
#     ds['ROAD'] + \
#     ds['BLD'] + \
#     ds['VEGH'] + \
#     ds['VEGB'] + \
#     ds['WATER']

# # # Counts of unique values
# var_name = 'BUILDING_FRACTION'
# fn_rdp = f"/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/" \
#          f"input/transfer_5185053_files_5895bb43/OSM_MNH_100m_{var_name}_LAT_LON.txt"
# df = pd.read_csv(fn_rdp, sep=' ', header=None)
# df.columns = ['Lat', 'Lon', 'Var']
# #print(df_BF['Lon'].value_counts())
#
# df_crop = crop_rdp(df, fn_lcz)
#
# # Area that has no values in grid
# xmin = 2.2445; xmax = 2.2447
# ymin = 48.852; ymax = 48.857
#
# df_nan = df_crop[
#     (df_crop.Lat > ymin) & (df_crop.Lat < ymax) &
#     (df_crop.Lon > xmin) & (df_crop.Lon < xmax)
#     ]
# print(df_nan)

