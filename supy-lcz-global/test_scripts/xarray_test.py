import os
import pandas as pd
import numpy as np
from pathlib import Path
from pyproj import CRS
from pyproj import Transformer
import xarray as xr

# os.chdir('/home/zcfaada@ad.ucl.ac.uk/Documents/UrbClimUGdissert/supy-lcz-global')
os.chdir(r"C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global")

split_site_list_df = pd.read_csv(Path('./resources/GreaterKL-2017_Y1_M2sp_3sf_R1_splitlist.csv'))
split_site_list_df.index.name = 'sitename'

site_prefix = r'GreaterKL-2017_Y1_M2sp_3sf_R1'
output_file = r'./data/consolidated_outputs/'
variable_list = ['Kdown', 'Kup', 'Ldown', 'Lup', 'Tsurf', 'QN', 'QF', 'QS', 'QH', 'QE', 'QHlumps', 'QElumps', 'QHresis', 'AlbBulk', 'Fc', 'Ts', 'T2', 'Q2', 'U10', 'RH2']
cover_list = ['LCZ1', 'LCZ2', 'LCZ3', 'LCZ4', 'LCZ5', 'LCZ6', 'LCZ7', 'LCZ8', 'LCZ9', 'LCZ10', 'LCZ11', 'LCZ12', 'LCZ13', 'LCZ14', 'LCZ15', 'LCZ16', 'LCZ17', 'Paved (-)', 'Buildings (-)', 'Grass (-)', 'Deciduous trees (-)', 'Evergreen trees (-)', 'Bare soil (-)', 'Water (-)', 'Mean building height (m)', 'Mean vegetation height (m)', 'Albedo (-)', 'Height-to-width ratio (-)', 'Frontal area index buildings (-)', 'Frontal area index deciduous tree (-)', 'Frontal area index evergeen tree (-)']

site_grid_length = 40

split_grid_length = 5
split_metre_length = 1000  * split_grid_length
split_file_count = 0
split_grid_area = split_grid_length**2

final_split_df = pd.MultiIndex(levels=[[],[]],
                       codes=[[],[]], names=[u'grid', u'timestamp'])

final_split_df = pd.DataFrame(index = final_split_df, columns = variable_list)
final_split_df = final_split_df.rename_axis(columns='var')

final_split_surf_frac = pd.DataFrame(columns = cover_list)
final_split_surf_frac.index.name = 'grid'

# grid and timestamp format for xarray to understand

final_split_df.index = final_split_df.index.set_levels(final_split_df.index.levels[0].astype('int64'), level=0)
final_split_df.index = final_split_df.index.set_levels(final_split_df.index.levels[1].astype('datetime64[ns]'), level=1)

lat_list = []
lon_list = []

for individual_split_site in split_site_list_df.index:

    individual_split_name = split_site_list_df.iloc[individual_split_site, 0]
    individual_split_path = f'data/{individual_split_name}/output/grid'
    individual_split_df = pd.read_hdf(Path(individual_split_path, 'df_output_uMF_uLCu.h5'))
    individual_split_lcz = pd.read_csv(Path(individual_split_path, 'df_roi_lcz.csv'), index_col = 'id')
    individual_split_supyfraction = pd.read_csv(Path(individual_split_path, 'df_roi_suews.csv'), index_col = 'id')
        
    individual_split_surf_frac = pd.merge(individual_split_lcz, individual_split_supyfraction, on = 'id')
        
    # convert latlong to UTM for consistency / ease of calculations

    split_site_lat = split_site_list_df.iloc[individual_split_site, 1]
    split_site_lon = split_site_list_df.iloc[individual_split_site, 2]
    
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

    # repeat latlong to form a 1d grid
    split_grid_xx, split_grid_yy = np.meshgrid(grid_midpoint_lat, grid_midpoint_lon)

    split_grid_lat = list(np.ndarray.flatten(split_grid_xx))
    split_grid_lon = list(np.ndarray.flatten(split_grid_yy))
    
    lat_list.extend(split_grid_lat) 
    lon_list.extend(split_grid_lon)

    file_grid_number = individual_split_df.index.levels[0]
    modified_grid_numbers = file_grid_number + (split_file_count * split_grid_area)
    grid_number_dict = dict(list(zip(file_grid_number.to_list(), modified_grid_numbers.to_list())))
    
    individual_split_df.rename(grid_number_dict, level = 'grid', inplace = True)
    individual_split_df.index.rename(['grid', 'timestamp'], inplace = True)

    individual_split_surf_frac.rename(index = grid_number_dict, inplace = True)
    individual_split_surf_frac.insert(0, 'latitude', split_grid_lat)
    individual_split_surf_frac.insert(1, 'longitude', split_grid_lon)
    
    print(f'Processing output file for {individual_split_name}')

    # merging to final df
    final_split_surf_frac = pd.concat([final_split_surf_frac, individual_split_surf_frac], join = 'inner')
    final_split_df = pd.concat([final_split_df, individual_split_df], join = 'inner')
    
    split_file_count += 1


final_split_df.to_hdf(Path(output_file, site_prefix + '_consolidated.h5'), key='df', mode = 'w')
final_split_surf_frac.to_csv(Path(output_file, site_prefix + '_attributes.csv'), mode = 'w')


# netCDF conversion

final_split_ds = xr.Dataset.from_dataframe(final_split_df)

final_split_ds = final_split_ds.assign_coords(latitude = ('grid', lat_list))
final_split_ds = final_split_ds.assign_coords(longitude = ('grid', lon_list))


print(final_split_ds)
final_split_ds.to_netcdf(path = Path(output_file, site_prefix + '_consolidated.nc'), mode ='w')


# need to rewrite or look at the re-meshing algorithm to take into account chunked runs and so the coordinates go left-down every split run
# most likely that the meshgrid doesnt take itno this "chunking" and misaligns the data

# alternative data structure with 2D meshgrid instead
# final_split_ds = xr.open_dataset(Path(output_file, site_prefix + '_consolidated.nc'))

final_split_ds = final_split_ds.sortby(['longitude', 'latitude','timestamp'])

nlat, nlon = site_grid_length, site_grid_length

lat_2d = final_split_ds['latitude'].values.reshape((nlat, nlon))
lon_2d = final_split_ds['longitude'].values.reshape((nlat, nlon))

data_vars = {}
for var_label in variable_list:
        flat_data = final_split_ds[var_label].values #need to instead obtain data directly from dataset 
        data_reshaped = flat_data.reshape(-1, nlat, nlon)
        data_vars[var_label] = (("timestamp","lat", "lon"), data_reshaped)
        
unflattened_final_ds = xr.Dataset(data_vars,
                                  coords = {
        'timestamp': final_split_ds['timestamp'],
        'latitude': (('lat', 'lon'), lat_2d),
        'longitude': (('lat', 'lon'), lon_2d)
    }
)

# =============================================================================
# data_vars = {}
# flat_data = {}
# for var_label in variable_list:
#         var_da = final_split_ds[var_label]
#         var_da = var_da.set_index(grid=["latitude", "longitude"])
#         var_da = var_da.sortby(['longitude', 'latitude','timestamp'])
#         
#         for lat, lon in var_da['latitude'].values, var_da['longitude'].values :
#             flat_data.extend(
#                 var_da.sel(latitude = lat, longitude = lon))
#         
#         data_reshaped = flat_data.reshape(-1, nlat, nlon)
#         data_vars[var_label] = (("timestamp","lat", "lon"), data_reshaped)
#         
#         unflattened_final_ds = xr.Dataset(data_vars,
#                                   coords = {
#         'timestamp': final_split_ds['timestamp'],
#         'latitude': (('lat', 'lon'), lat_2d),
#         'longitude': (('lat', 'lon'), lon_2d)
#     }
# )
# =============================================================================

# WIP 
# =============================================================================
# data_vars = {}
# flat_data = np.empty(1600, 11185)
# 
# for var_label in variable_list:
#         var_da = final_split_ds[var_label]
#         var_da = var_da.set_index(grid=["latitude", "longitude"])
#         var_da = var_da.sortby(['longitude', 'latitude','timestamp'])
#         
#         for lon in var_da['longitude'].values:
#             flat_data = np.append(flat_data,
#                 var_da.sel(longitude = lon))
#                    
#         data_reshaped = flat_data.reshape(-1, nlat, nlon)
#         data_vars[var_label] = (("timestamp","lat", "lon"), data_reshaped)
#         
#         unflattened_final_ds = xr.Dataset(data_vars,
#                                   coords = {
#         'timestamp': final_split_ds['timestamp'],
#         'latitude': (('lat', 'lon'), lat_2d),
#         'longitude': (('lat', 'lon'), lon_2d)
#     }
# )
# 
# =============================================================================
print(unflattened_final_ds)

unflattened_final_ds.to_netcdf(path = Path(output_file, site_prefix + '_unflattened.nc'), mode = 'w')

# lat_val = final_split_ds.coords['latitude']
# lon_val = final_split_ds.coords['longitude']
# print(lat_val, lon_val)




