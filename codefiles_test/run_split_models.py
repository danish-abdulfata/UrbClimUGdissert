import time
import os
import errno
from pathlib import Path
import pandas as pd
import numpy as np
import xarray as xr
from pyproj import CRS
from pyproj import Transformer
from runner.runner import main as run_runner

# ------------------------------------------------ Model Parameters and Setup --------------------------------------------------
# change values as needed, valid ranges in quickstart.md
# REMEMBER TO CHANGE site_prefix AND/OR DELETE ./data and ./resources FILES BEFORE STARTING!

# Site Information
site_prefix = "GreaterKL-2017_Y1_M2sp_3sf_R3" # CHANGE NAME BEFORE RUN
site_midpoint_lat = 3.056577
site_midpoint_lon = 101.617373

#site_midpoint_lat = 3.056577
#site_midpoint_lon = 101.617373
# current way I name: [sitename]-time_[unit][length]_[unit][spinup length]sp_[splitfactor]sf_(run number)

# Model 
measurement_height_above_ground = 100
surface_cover_radius = 1000 
time_analysis_start = "2016-10-03 00:00:00"
time_coverage_end = "2018-01-12 00:00:00"
timestep_interval_seconds = 3600
local_utc_offset_hours = 8

# Spinup false by default. check run_runner below at end of 2nd part of script.
# Change default spinup (2 years) in runner.py at line 868

# grid_boxes
site_grid_length = 40

# By what factor should the area be divided, ie. 2^2(split_factor) models will sequentially run.   
# In other words, split models will run with 1 = 1/4, 2 = 1/4^2, 3 = 1/4^3, etc, number of grids.
split_factor = 3

##### What variables should be saved?
"""
    Full Variable List 
    
    ['Kdown', 'Kup', 'Ldown', 'Lup', 'Tsurf', 'QN', 'QF', 'QS', 'QH', 'QE', 'QHlumps', 'QElumps', 'QHresis', 'Rain', 
                    'Irr', 'Evap', 'RO', 'TotCh', 'SurfCh', 'State', 'NWtrState', 'Drainage', 'SMD', 'FlowCh', 'AddWater', 
                    'ROSoil', 'ROPipe', 'ROImp', 'ROVeg', 'ROWater', 'WUInt', 'WUEveTr', 'WUDecTr', 'WUGrass', 'SMDPaved', 
                    'SMDBldgs', 'SMDEveTr', 'SMDDecTr', 'SMDGrass', 'SMDBSoil', 'StPaved', 'StBldgs', 'StEveTr', 'StDecTr', 
                    'StGrass', 'StBSoil', 'StWater', 'Zenith', 'Azimuth', 'AlbBulk', 'Fcld', 'LAI', 'z0m', 'zdm', 'UStar', 
                    'Lob', 'RA', 'RS', 'Fc', 'FcPhoto', 'FcRespi', 'FcMetab', 'FcTraff', 'FcBuild', 'FcPoint', 'QNSnowFr', 
                    'QNSnow', 'AlbSnow', 'QM', 'QMFreeze', 'QMRain', 'SWE', 'MeltWater', 'MeltWStore', 'SnowCh', 'SnowRPaved', 
                    'SnowRBldgs', 'Ts', 'T2', 'Q2', 'U10', 'RH2']
    
    https://suews.readthedocs.io/en/latest/output_files/output_files.html, variable meanings

"""
# 'SUEWS' model outputs
variable_list = ['Kdown', 'Kup', 'Ldown', 'Lup', 'Tsurf', 'QN', 'QF', 'QS', 'QH', 'QE', 'QHlumps', 'QElumps', 'AlbBulk', 'T2', 'Q2', 'U10', 'RH2']


# cover fractions of  model grids
cover_list = ['LCZ1', 'LCZ2', 'LCZ3', 'LCZ4', 'LCZ5', 'LCZ6', 'LCZ7', 'LCZ8', 'LCZ9', 'LCZ10', 
              'LCZ11', 'LCZ12', 'LCZ13', 'LCZ14', 'LCZ15', 'LCZ16', 'LCZ17',
              'Paved (-)', 'Buildings (-)', 'Grass (-)', 'Deciduous trees (-)', 'Evergreen trees (-)', 'Bare soil (-)', 
              'Water (-)', 'Mean building height (m)', 'Mean vegetation height (m)', 'Albedo (-)', 'Height-to-width ratio (-)', 
              'Frontal area index buildings (-)', 'Frontal area index deciduous tree (-)', 'Frontal area index evergeen tree (-)']


#%%
# ------------------------------------------------------ script starts here ------------------------------------------------------

##################################################### 1st part of script #####################################################
########### Processing input paramaters


run_split_models_start = time.time()

# Split factor check if it's valid

# Total area covered will be grid_metre_length^2 * grid_boxes, in m^2, same as surface_cover_radius
grid_metre_length = surface_cover_radius 

site_grid_area = site_grid_length ** 2

site_split_length = 2 ** split_factor
number_of_runs = site_split_length ** 2

split_grid_area = site_grid_area / number_of_runs
split_grid_length = int(site_grid_length / site_split_length)

try:
    (site_grid_area) % number_of_runs == 0
except:
    raise ValueError(f"Total number of grids per run ({site_grid_area}) must be divisible by 2^2(split_factor) ({number_of_runs}) to maintain identical square model areas")
else:
    print(f"Split factor of {split_factor} is valid. Site will be split into {number_of_runs} runs at {split_grid_area} grids per run")

# Geodesic calculations modified from utils.py to maintain consistency

crs_dict = {
            'proj': 'utm',
            'zone': int(np.round((183 + site_midpoint_lon) / 6)),
            'south': site_midpoint_lat < 0,
        }

crs = CRS.from_dict(crs_dict)

# convert latlong to UTM for consistency / ease of calculations
to_utm = Transformer.from_crs(crs_from='EPSG:4326', crs_to=crs)
site_midpoint_x, site_midpoint_y = to_utm.transform(xx=site_midpoint_lat, yy=site_midpoint_lon)

# identify site boundaries
site_metre_length = grid_metre_length  * site_grid_length

site_y_max = site_midpoint_y + (site_metre_length / 2)
site_y_min = site_y_max - (site_metre_length)
site_x_max = site_midpoint_x + (site_metre_length / 2)
site_x_min = site_x_max - (site_metre_length)

# +1 to account for the additional sample at the start, [1:] to remove before meshing.
split_midpoint_x = np.linspace(site_x_min, site_x_max, site_split_length + 1, endpoint = False)[1:]
split_midpoint_y = np.linspace(site_y_min, site_y_max, site_split_length + 1, endpoint = False)[1:]

# converting back to latlong
from_utm = Transformer.from_crs(crs_from=crs, crs_to='EPSG:4326')
split_midpoint_lat, split_midpoint_lon = from_utm.transform(xx=split_midpoint_x, yy=split_midpoint_y)

# repeat latlong to form a 2d grid
split_xx, split_yy = np.meshgrid(split_midpoint_lat, split_midpoint_lon)

# converts flattened nparrays to lists, and rounding 
lat_list = list(np.ndarray.flatten(split_xx))
lon_list = list(np.ndarray.flatten(split_yy))

# lat_list =  [ round(elem, 5) for elem in lat_list]
# lon_list =  [ round(elem, 5) for elem in lon_list]

# Modified from create_supy_sitelist
split_site_list = []

# adds number_of_runs index names to list. 
for split_affix in range(1, number_of_runs + 1):
    split_site_list.append(site_prefix + "_s" + str(split_affix))
 
# creates dataframe with index column only
split_site_list_df = pd.DataFrame(index=split_site_list)
split_site_list_df.index.name = 'sitename'

# add specified latlong column headers and data to df
split_site_list_df.insert(0, 'latitude', lat_list)
split_site_list_df.insert(1, 'longitude', lon_list)

# values that won't change for every split
column_dict = {'measurement_height_above_ground': measurement_height_above_ground,
            'surface_cover_radius': surface_cover_radius,
            'time_analysis_start': time_analysis_start,
            'time_coverage_end': time_coverage_end,
            'timestep_interval_seconds': timestep_interval_seconds,
            'local_utc_offset_hours': local_utc_offset_hours}

# for loop to add parameters and their columns into data frame df.
column_index = 2
for column_key, column_value in column_dict.items():
    split_site_list_df.insert(column_index, column_key, column_value)
    column_index += 1
    
# create .csv file at specified filepath
split_site_list_file = Path(f'resources/{site_prefix}_splitlist.csv')
split_site_list_df.to_csv(split_site_list_file)

try:
    split_site_list_file.exists()
except:
    raise Exception(f"----> {site_prefix}_custom.csv failed to generate")
else:
    print(f"--------> {site_prefix}_custom.csv successfully created. Starting SuPy models...")


#%%
##################################################### 2nd part of script #####################################################
########### Run SuPy runner.runner script for all split sites using processed inputs.

# modified from batch_simulations_buffer.py

split_run_count = 0
for individual_split_site in split_site_list_df.index:
    run_runner([individual_split_site,
            '--run-type', 'grid',
            '--grid-size', str(grid_metre_length),
            '--grid-boxes', str(split_grid_length),
            '--metforc-src', 'era5land', # change if needed
            '--urbdesc-src', 'lcz_updated', #  change if needed
            '--sitelist', f'{site_prefix}_splitlist',
            '--download-era5']) # removed --do-spinup to disable spinup
    split_run_count += 1
    print(f"=======> {individual_split_site} completed, #{split_run_count} out of #{number_of_runs} for {site_prefix} <========")

run_split_models_end = time.time()
runtime_models = (run_split_models_end - run_split_models_start)
runtime_models_in_min = divmod(runtime_models, 60)

print(f"========================> Total model runtime: {int(runtime_models_in_min[0])} min(s) and {runtime_models_in_min[1]:.2f} sec <========================")
# raise SystemExit()

for individual_split_site in split_site_list_df.index:
    individual_split_path = Path(f'data/{individual_split_site}/output/grid')
    split_output_file = individual_split_path / 'df_output_uMF_uLCu.h5'
    if not split_output_file.exists():
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), str(split_output_file))

print(f"Output .h5 files for all {number_of_runs} runs successfully generated.")

#%%
##################################################### 3rd part of script #####################################################
######### Consolidate/process output files into one singular file

output_file = r'./data/consolidated_outputs/'

# Initializing dataframes

final_split_df = pd.MultiIndex(levels=[[],[]],
                       codes=[[],[]], names=[u'grid', u'timestamp'])

final_split_df = pd.DataFrame(index = final_split_df, columns = variable_list)
final_split_df = final_split_df.rename_axis(columns='var')

final_split_surf_frac = pd.DataFrame(columns = cover_list)
final_split_surf_frac.index.name = 'grid'

final_df = pd.MultiIndex(levels=[[],[],[]],
                       codes=[[],[],[]], names=[u'timestamp', u'latitude', u'longitude'])

final_df = pd.DataFrame(index = final_df, columns = variable_list)
final_df = final_df.rename_axis(columns='var')

# MultiIndex formats for xarray to understand

final_split_df.index = final_split_df.index.set_levels(final_split_df.index.levels[0].astype('int64'), level=0)
final_split_df.index = final_split_df.index.set_levels(final_split_df.index.levels[1].astype('datetime64[ns]'), level=1)

final_df.index = final_df.index.set_levels(final_df.index.levels[0].astype('datetime64[ns]'), level=0)
final_df.index = final_df.index.set_levels(final_df.index.levels[1].astype('float64'), level=1)
final_df.index = final_df.index.set_levels(final_df.index.levels[2].astype('float64'), level=2)

# Intializing latlon lists

grid_lat_list = []
grid_lon_list = []

split_metre_length = 1000  * split_grid_length
split_file_count = 0

for individual_split_site in split_site_list_df.index:

    individual_split_path = f'data/{individual_split_site}/output/grid'
    individual_split_df = pd.read_hdf(Path(individual_split_path, 'df_output_uMF_uLCu.h5'))
    individual_split_lcz = pd.read_csv(Path(individual_split_path, 'df_roi_lcz.csv'), index_col = 'id')
    individual_split_supyfraction = pd.read_csv(Path(individual_split_path, 'df_roi_suews.csv'), index_col = 'id')
        
    individual_split_surf_frac = pd.merge(individual_split_lcz, individual_split_supyfraction, on = 'id')
        
    # convert latlong to UTM for consistency / ease of calculations

    split_site_lat = split_site_list_df.at[individual_split_site, 'latitude']
    split_site_lon = split_site_list_df.at[individual_split_site, 'longitude']
    
    crs_dict = {
                'proj': 'utm',
                'zone': int(np.round((183 + split_site_lon) / 6)),
                'south':  split_site_lat < 0,
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
    grid_midpoint_lat = np.flip(grid_midpoint_lat)
    grid_midpoint_lon = np.flip(grid_midpoint_lon)

    # repeat latlong to form a 1d grid
    split_grid_yy, split_grid_xx = np.meshgrid(grid_midpoint_lat, grid_midpoint_lon)

    split_grid_lat = list(np.ndarray.flatten(split_grid_yy))
    split_grid_lon = list(np.ndarray.flatten(split_grid_xx))
    
    #rounded
    #split_grid_lat =  [ round(elem, 5) for elem in split_grid_lat]
    #split_grid_lon =  [ round(elem, 5) for elem in split_grid_lon]
    
    grid_lat_list.extend(split_grid_lat) 
    grid_lon_list.extend(split_grid_lon)

    file_grid_number = individual_split_df.index.levels[0]
    modified_grid_numbers = file_grid_number + (split_file_count * split_grid_area)
    grid_number_dict = dict(list(zip(file_grid_number.to_list(), modified_grid_numbers.to_list())))
    
    individual_split_df.rename(grid_number_dict, level = 'grid', inplace = True)
    individual_split_df.index.rename(['grid', 'timestamp'], inplace = True)

    individual_split_surf_frac.rename(index = grid_number_dict, inplace = True)
    individual_split_surf_frac.insert(0, 'latitude', split_grid_lat)
    individual_split_surf_frac.insert(1, 'longitude', split_grid_lon)
    
    print(f'Processing output file for {individual_split_site}')

    # merging to final df
    final_split_surf_frac = pd.concat([final_split_surf_frac, individual_split_surf_frac], join = 'inner')
    final_split_df = pd.concat([final_split_df, individual_split_df], join = 'inner')
    
    # another df with coord data instead
    individual_split_df_coords = individual_split_df.reset_index(level=0, drop = True)
    
    split_latlon_iter = int(individual_split_df.shape[0] / len(split_grid_lat))
    split_grid_lat_iter = split_grid_lat * split_latlon_iter
    split_grid_lon_iter = split_grid_lon * split_latlon_iter
    
    individual_split_df_coords.set_index([split_grid_lat_iter, split_grid_lon_iter], append = True, inplace = True)
    individual_split_df_coords.index.rename(['timestamp', 'latitude', 'longitude'], inplace = True)
    final_df = pd.concat([final_df, individual_split_df_coords], join = 'inner')
    
    split_file_count += 1

######## Output Files

# attribute file
final_df.to_hdf(Path(output_file, site_prefix + '_consolidated.h5'), key='df', mode = 'w')
final_split_surf_frac.to_csv(Path(output_file, site_prefix + '_attributes.csv'), mode = 'w')

# netCDF conversion
final_ds = xr.Dataset.from_dataframe(final_split_df)

final_ds = final_ds.assign_coords(latitude = ('grid', grid_lat_list))
final_ds = final_ds.assign_coords(longitude = ('grid', grid_lon_list))

final_ds.to_netcdf(path = Path(output_file, site_prefix + '_consolidated.nc'), mode ='w')

# alternative data structure with 2D meshgrid instead
# very werid and complicated mapping - the 2d arrays map to each grid, for example, 2nd cell in the 1st column of 2d_lat and 2d_lon represent Grid #?
# clearly there has been data like this before but i am still confused

# in the end it matches the variable data and grid coordinate correctly, but seems a little sussy

final_ds_sort = final_ds.sortby(['longitude', 'latitude'])

nlat, nlon = site_grid_length, site_grid_length

lat_2d = np.array(grid_lat_list).reshape(nlat, nlon)
lon_2d = np.array(grid_lon_list).reshape(nlat, nlon)

data_vars = {}
for var_label in variable_list:
        flat_data = final_ds_sort[var_label].values
        data_reshaped = flat_data.reshape(nlat, nlon, -1)
        data_vars[var_label] = (("y", "x", "timestamp"), data_reshaped)
 
    
# unflattened ds with only (timestamp, latitude, longitude) dimensions
final_ds_unflattened = xr.Dataset(data_vars,
                                  coords = {
        'timestamp': final_ds_sort['timestamp'],
        'latitude': (('y', 'x'), lat_2d),
        'longitude': (('y', 'x'), lon_2d)})

final_ds_unflattened.to_netcdf(path = Path(output_file, site_prefix + '_unflattened.nc'), mode = 'w')

##################################################### End of main script #####################################################


# Final countdown
run_script_end = time.time()
runtime_script = (run_script_end - run_split_models_start)
runtime_script_in_min = divmod(runtime_models, 60)

print(f"========================> Total model runtime: {int(runtime_models_in_min[0])} min(s) and {runtime_models_in_min[1]:.2f} sec <========================")
print(f"========================> Total script runtime: {int(runtime_script_in_min[0])} min(s) and {runtime_script_in_min[1]:.2f} sec <========================")
