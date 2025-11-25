# -*- coding: utf-8 -*-
import pandas as pd
import os
import numpy as np
import xarray as xr
from pathlib import Path
from pyproj import Transformer
from pyproj import CRS

# troubleshooting site area mismatch.

####### standadrd variables
os.chdir(r"C:\Users\ahmad\Documents\UrbClimUGdissert\supy-lcz-global")
output_file = './data/consolidated_outputs/'
site_prefix = "GreaterKL-2017_Y1_M2sp_3sf_R1"
data = Path(output_file, site_prefix + '_attributes.csv')
df = pd.read_csv(data)

site_prefix = "GreaterKL-2017_Y1_M2sp_3sf_R1" # CHANGE NAME BEFORE RUN
site_midpoint_lat = 3.056577
site_midpoint_lon = 101.617373

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
dist_boundary = (split_grid_length * grid_metre_length) / 2

site_y_max = site_midpoint_y + (site_metre_length / 2) - dist_boundary
site_y_min = site_midpoint_y - (site_metre_length /2) + dist_boundary
site_x_max = site_midpoint_x + (site_metre_length / 2) - dist_boundary
site_x_min = site_midpoint_x - (site_metre_length /2) + dist_boundary

# +1 to account for the additional sample at the start
split_midpoint_x = np.linspace(site_x_min, site_x_max, site_split_length, endpoint = True)
split_midpoint_y = np.linspace(site_y_min, site_y_max, site_split_length, endpoint = True)

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

# After all coordinate calculations in consolidation
all_lats = split_site_list_df['latitude'].values
all_lons = split_site_list_df['longitude'].values

from geopy.distance import geodesic

# Calculate actual diagonal using geodesic
sw_corner = (min(all_lats), min(all_lons))
ne_corner = (max(all_lats), max(all_lons))
nw_corner = (max(all_lats), min(all_lons))
se_corner = (min(all_lats), max(all_lons))

diagonal1 = geodesic(sw_corner, ne_corner).km
diagonal2 = geodesic(nw_corner, se_corner).km
side_ns = geodesic(sw_corner, nw_corner).km
side_ew = geodesic(sw_corner, se_corner).km

print(f"Actual measurements:")
print(f"North-South side: {side_ns:.2f} km")
print(f"East-West side: {side_ew:.2f} km") 
print(f"Diagonal 1 (SW-NE): {diagonal1:.2f} km")
print(f"Diagonal 2 (NW-SE): {diagonal2:.2f} km")
print(f"Calculated area: {side_ns * side_ew:.2f} km²")

    
