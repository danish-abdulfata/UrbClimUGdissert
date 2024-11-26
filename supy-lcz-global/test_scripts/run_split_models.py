import time
from pathlib import Path
import pandas as pd
import numpy as np
from pyproj import CRS
from pyproj import Transformer
from runner.runner import main as run_runner
from test_scripts.structure_grid_output import main as run_structure_grid_output
import test_scripts.structure_grid_output as grid_out

# ------------------------------------------------ Model Parameters and Setup --------------------------------------------------
# change values as needed, valid ranges in quickstart.md

# Site Information
site_prefix = "KL-KualaLumpur-2017_1Msp_2sf_r2"
site_midpoint_lat = 3.056577
site_midpoint_lon = 101.617373
# current way I name: Kl-KualaLumpur-[year]_[spinup length]_[splitfactor]_[run number]

# Model 
measurement_height_above_ground = 100
surface_cover_radius = 1000 
time_analysis_start = "2016-12-01 00:00:00"
time_coverage_end = "2017-01-11 00:00:00"
timestep_interval_seconds = 3600
local_utc_offset_hours = 8

# Spinup true by default. check run_runner below at end of 2nd part of script.
# Change default spinup (2 years) in runner.py at line 868

# Total area covered will be grid_size^2 * grid_boxes, in m^2
# grid_size
grid_metre_length = 1000 

# grid_boxes
site_grid_length = 40

# By what factor should the area be divided, ie. 2^2(split_factor) models will sequentially run.   
# In other words, split models will run with 1 = 1/4, 2 = 1/4^2, 3 = 1/4^3, etc, number of grids.
split_factor = 2

# ------------------------------------------------ script starts here --------------------------------------------------

################################ 1st part of script ################################
########### Processing input paramaters

run_split_models_start = time.time()

# Split factor check if it's valid

site_grid_area = site_grid_length ** 2

site_split_length = 2 ** split_factor
number_of_runs = site_split_length ** 2

split_grid_area = site_grid_area / number_of_runs
split_grid_length = int(site_grid_length / site_split_length)

try:
    (site_grid_length) % split_grid_length == 0
except:
    raise ValueError(f"Total number of grids ({site_grid_area}) must be divisible by 2^2(split_factor) ({number_of_runs}) to maintain identical square model areas")
else:
    print(f"Split factor of {split_factor} is valid. Site will be split into {number_of_runs} runs at {split_grid_area} grids per run")

#raise SystemExit()
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

# repeat latlong to form a 1d grid
split_xx, split_yy = np.meshgrid(split_midpoint_lat, split_midpoint_lon)

def flatten(l):
  out = []
  for item in l:
    if isinstance(item, (list, tuple)):
      out.extend(flatten(item))
    else:
      out.append(item)
  return out

# converts nparrays to nested lists which then get converted to flattened lists
lat_list = flatten(split_xx.tolist())
lon_list = flatten(split_yy.tolist())

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
    tb = sys.exception().__traceback__
    raise Exception(f"----> {site_prefix}_custom.csv failed to generate").with_traceback(tb)
else:
    print(f"--------> {site_prefix}_custom.csv successfully created. Starting SuPy models...")
    
# raise SystemExit()
################################ 2nd part of script ################################
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
            '--download-era5']) # remove --do-spinup to disable spinup
    split_run_count += 1
    print(f"=======> {individual_split_site} completed, #{split_run_count} out of #{number_of_runs} for {site_prefix} <========")

run_split_models_end = time.time()
runtime = (run_split_models_end - run_split_models_start)
runtime_in_min = divmod(runtime / 60)

print(f"========================> Total runtime: {runtime_in_min[0]:.2f} min(s) and {runtime_in_min[1]:.2f} <========================")

################################ 4th part of script ################################
########### Consolidate/process output files into one singular file

for individual_split_site in split_site_list_df.index:

    individual_split_name = split_site_list_df.iloc[individual_split_site, 0]
    individual_split_lat = split_site_list_df.iloc[individual_split_site, 1]
    individual_split_lon = split_site_list_df.iloc[indvidual_split_site, 2]
    
    individual_split_path = f'data/{individual_split_name}/output/grid'
    
    grid_out.convert_h5_to_netcdf(individual_split_path + '/df_output_uMF_uLCu.h5'), 1000, individual_split_lat, individual_split_lon)
    split_run_count += 1
    
    
    print(f"=======> {individual_split_site} output conversion complete, #{split_run_count} out of #{number_of_runs} for {site_prefix} <========")
