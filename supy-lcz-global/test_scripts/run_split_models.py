import os
os.environ['USE_PYGEOS'] = '0'

from pathlib import Path
import pandas as pd
import numpy as np
from pyproj import CRS
from pyproj import Transformer

# Model Parameters

# Site Information
sitename = "KL-KualaLumpur"
site_midpoint_lat = 3.056577
site_midpoint_lon = 101.617373

measurement_height_above_ground = 100
surface_cover_radius = 1000 
time_analysis_start = "2016-01-01 00:00:00"
time_coverage_end = "2017-01-01 00:00:00"
timestep_interval_seconds = 3600
local_utc_offset_hours = 8

# spinup = true
# need to check further;
# modify runner script so that we can define spinup here?

# Total area covered will be grid_size * grid_boxes, in m^2
grid_size = 1000 
grid_boxes = 40

# By what factor should the area be divided, 1 = 1/4, 2 = 1/4^2, 3 = 1/4^3 and etc, to maintain square study area for compatibility with utils.py.   
split_factor = 2
# 2, 4, 8, 16

# modified from utils.py to maintain consistency with geodesic calculations
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

split_midpoint_y = np.linspace(site_y_min, site_y_max, (2**split_factor) + 1, endpoint = False)
split_midpoint_x = np.linspace(site_x_min, site_x_max, (2**split_factor) + 1, endpoint = False)

split_xx, split_yy = np.meshgrid(split_midpoint_y, split_midpoint_x)

print("Site min and max points")
print(site_midpoint_y)
print(site_midpoint_x)

print("Site midpoints")
print(split_xx)
print(split_yy)

# copied from utils.py
# def from_point(
#            cls,
#            *,
#            lon: float,
#           lat: float,
#            nx: int,
#            dx: float,
#            target_crs: CRS = CRS('EPSG:4326'),
#    ) -> Grid:
#        crs_dict = {
#            'proj': 'utm',
#            'zone': int(np.round((183 + lon) / 6)),
#            'south': lat < 0,
#        }
#        crs = CRS.from_dict(crs_dict)
#        to_utm = Transformer.from_crs(crs_from='EPSG:4326', crs_to=crs)
#        x_m, y_m = to_utm.transform(xx=lat, yy=lon)
#
#        y_m_max = y_m + (nx / 2 * dx)
#        y_m_min = y_m_max - ((nx - 1) * dx)
#        x_m_max = x_m + (nx / 2 * dx)
#        x_m_min = x_m_max - ((nx - 1) * dx)
#
#        y_m = np.linspace(y_m_min, y_m_max, nx)
#        x_m = np.linspace(x_m_min, x_m_max, nx)
#        xx, yy = np.meshgrid(y_m, x_m)
#        
#        
#  
#        polygons = (
#            Polygon(
#                [(y - dx, x), (y - dx, x - dx), (y, x - dx), (y, x)],
#            ) for x, y in zip(xx.ravel(), yy.ravel())
#        )
#        grid = gpd.GeoDataFrame({'geometry': polygons})
#        grid.index.name = 'id'
#        # the stupid georasters thing does only work if there is some column
#        grid['some_col'] = 1
#        grid = grid.set_crs(crs)
#        grid = grid.to_crs(target_crs)
#        return cls(gdf=grid, shape=(nx, nx), step=dx, crs=target_crs)





