import os
os.environ['USE_PYGEOS'] = '0'

from pathlib import Path
import pandas as pd
import numpy as np
from pyproj import CRS
from pyproj import Transformer

# Model Parameters

# Site area
site_midpoint_lat = 3.056577
site_midpoint_lon = 101.617373

# Total area covered will be grid_size * grid_boxes, in m^2
grid_size = 1000 
grid_boxes = 40

# By what factor should the area be divided, 1 = 1/4, 2 = 1/4^2, 3 = 1/4^3 etc, MAINTAINING SQUARE STUDY AREA.   
factor = 2

crs_dict = {
            'proj': 'utm',
            'zone': int(np.round((183 + site_midpoint_lon) / 6)),
            'south': site_midpoint_lat < 0,
        }

crs = CRS.from_dict(crs_dict)
to_utm = Transformer.from_crs(crs_from='EPSG:4326', crs_to=crs)
site_midpoint_x, site_midpoint_y = to_utm.transform(xx=site_midpoint_lat, yy=site_midpoint_lon)

distance_from_midpoint = grid_size * grid_boxes / 2

site_y_max = site_midpoint_y + (distance_from_midpoint)
site_y_min = site_y_max - ((grid_boxes - 1) * grid_size)
site_x_max = site_midpoint_x + (distance_from_midpoint)
site_x_min = site_x_max - ((grid_boxes - 1) * grid_size)

site_midpoint_y = np.linspace(site_y_min, site_y_max, 4**factor)
site_midpoint_x = np.linspace(site_x_min, site_x_max, 4**factor)

xx, yy = np.meshgrid(site_midpoint_y, site_midpoint_x)

print("Site min and max points")
print(site_midpoint_y)
print(site_midpoint_x)

print("Site midpoints")
print(xx)
print(yy)

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





