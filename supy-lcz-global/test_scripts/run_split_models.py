import os
os.environ['USE_PYGEOS'] = '0'

from pathlib import Path
import pandas as pd
import numpy as np
from pyproj import CRS
from pyproj import Transformer

# ----------------- Model Parameters and Setup ----------------
# change values as needed, valid ranges in quickstart.md

# Site Information
site_prefix = "KL-KualaLumpur"
site_midpoint_lat = 3.056577
site_midpoint_lon = 101.617373

# Model 
measurement_height_above_ground = 100
surface_cover_radius = 1000 
time_analysis_start = "2016-01-01 00:00:00"
time_coverage_end = "2017-01-01 00:00:00"
timestep_interval_seconds = 3600
local_utc_offset_hours = 8

# Change default spinup (2 years) in runner.py
spinup = True

# Total area covered will be grid_size^2 * grid_boxes, in m^2
grid_size = 1000 
grid_boxes = 40

# By what factor should the area be divided, ie. 4^split_factor models will sequentially be run.   
# In other words, split models will run with 1 = 1/4, 2 = 1/4^2, 3 = 1/4^3, etc, number of grids.
split_factor = 2



# --------------------- script starts here -------------------------
# Split factor check if it's valid

try:
(grid_boxes ** 2) % (2 ** split_factor) == 0:
except:
            raise ValueError("Total number of grids must be divisible by 2^split_factor to maintain identical square model areas")
             

# Geodesic calculations modified from utils.py to maintain consistency

crs_dict = {
            'proj': 'utm',
            'zone': int(np.round((183 + site_midpoint_lon) / 6)),
            'south': site_midpoint_lat < 0,
        }

crs = CRS.from_dict(crs_dict)

to_utm = Transformer.from_crs(crs_from='EPSG:4326', crs_to=crs)
site_midpoint_x, site_midpoint_y = to_utm.transform(xx=site_midpoint_lat, yy=site_midpoint_lon)

site_area_length = grid_size * grid_boxes

site_y_max = site_midpoint_y + (site_area_length / 2)
site_y_min = site_y_max - (site_area_length)
site_x_max = site_midpoint_x + (site_area_length / 2)
site_x_min = site_x_max - (site_area_length)

# +1 to account for the additional sample at the start, [1:] to remove before meshing.
split_midpoint_x = np.linspace(site_x_min, site_x_max, (2**split_factor) + 1, endpoint = False)[1:]
split_midpoint_y = np.linspace(site_y_min, site_y_max, (2**split_factor) + 1, endpoint = False)[1:]

# converting back to latlong
from_utm = Transformer.from_crs(crs_from=crs, crs_to='EPSG:4326')
split_midpoint_lat, split_midpoint_lon = from_utm.transform(xx=split_midpoint_x, yy=split_midpoint_y)

# repeat latlong to form a 1d grid
split_xx, split_yy = np.meshgrid(split_midpoint_lat, split_midpoint_lon)

# Display split outputs
# print("Site midpoint in UTM")
# print(site_midpoint_x, site_midpoint_y)

# print("Maximum and minimum x and y values")
# print(site_x_max, site_x_min, site_y_max, site_y_min)

# print("Split midpoints")
# print(split_midpoint_lat)
# print(split_midpoint_lon)

# print("Split midpoints matrix")
# print("---------> x split midpoints (latitiude)")
# print(split_xx)
# print("---------> y split midpoints (longitude)")
# print(split_yy)

# Modified from create_supy_sitelist
sitelist = []

# base 4 as there will be 4^split_factor coordinates. 
for split_affix in range(1, 4**split_factor + 1):
    sitelist.append(site_prefix + "_s" + str(split_affix))
 
# creates dataframe with index column only
df = pd.DataFrame(index=sitelist)
df.index.name = 'sitename'

# add latlong to dataframe

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

# add specified latlong columns and data to df
df.insert(0, 'latitude', lat_list)
df.insert(1, 'longitude', lon_list)

column_dict = {'measurement_height_above_ground': measurement_height_above_ground,
        'surface_cover_radius': surface_cover_radius,
        'time_analysis_start': time_analysis_start,
        'time_coverage_end': time_coverage_end,
        'timestep_interval_seconds': timestep_interval_seconds,
        'local_utc_offset_hours': local_utc_offset_hours}

# for loop to add parameters and their columns into data frame df . reversed() used because columns were placed from end to start.
column_index = 2
for column_key, column_value in reversed(column_dict.items()):
    df.insert(column_index, column_key, column_value)
    column_index += 1
    
# create .csv file at specified filepath
filename = Path(f'test_scripts/sitelist_custom.csv')
df.to_csv(filename)

if filename.exists():
    print("----> sitelist_custom.csv successfully created")
else: 
    print("----> sitelist_custom.csv failed to generate")

# 2nd part of script 

print("--------> Starting SuPy models...")