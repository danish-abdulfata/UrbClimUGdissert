# import time
import pandas as pd
import numpy as np
from pathlib import Path
from pyproj import CRS
from pyproj import Transformer
# import xarray as xr
# import errno
# import os
# from runner.runner import main as run_runner
############################# Testing for run_split_models.py, 2nd part.

split_runs_start = time.time()
split_site_list_df = pd.read_csv(Path('resources/GreaterKL-2017_Y1_M2sp_3sf_R1_splitlist.csv'))
split_site_list_df.index.name = 'sitename'
number_of_runs = 3
split_grid_length = 5
split_grid_area = split_grid_length**2
split_run_count = 0
site_prefix = "GreaterKL-2017_Y1_M2sp_3sf_R1"

# for individual_split_site in site_list:
    # run_runner([individual_split_site,
        # '--run-type', 'grid',
        # '--grid-size', '1000',
        # '--grid-boxes', str(split_grid_length),
        # '--metforc-src', 'era5land',
        # '--urbdesc-src', 'lcz_updated',
        # '--sitelist', f'{site_prefix}_splitlist',
        # '--download-era5',
        # '--do-spinup'])
    # split_run_count += 1
    # print(f"====> Split Run #{split_run_count} completed out of {number_of_runs} for {individual_split_site}") 
    # print(f"====> Split Run {individual_split_site} completed out of {number_of_runs} for site_name_prefix") 
        
# split_runs_end = time.time()
# print(f"==============> Total runtime: {(split_runs_end - split_runs_start):.2f} s <=================")

# for individual_split_site in site_list_df.index:
    # individual_split_name = split_site_df.iloc[individual_split_site, 0]
    # individual_split_lat = float(site_list_df.iloc[individual_split_site, 1])
    # individual_split_lon = float(site_list_df.iloc[individual_split_site, 2])
    # individual_split_path = f'data/{individual_split_name}/output/grid'
    # grid_out.convert_h5_to_netcdf(individual_split_path + '/df_output_uMF_uLCu.h5', 1000, individual_split_lat, individual_split_lon)
    # split_run_count += 1
    # hdf_file = pd.read_hdf(individual_split_path + '/df_output_uMF_uLCu_latlon.nc')
    # print(hdf_file)
    
    # print(f"=======> {individual_split_site} output conversion complete, #{split_run_count} out of #{number_of_runs} for {site_prefix} <========")

#  merging into one, output file with grid coordinates

# relabelling grid indexes testing

# model_run = 'KL-KualaLumpur-2017_1Msp_1_s1'
# test_out_df = pd.read_hdf(f'data/{model_run}/output/grid/df_output_uMF_uLCu.h5')
# print(test_out_df)

# print(test_out_df)

# defining list for all variables

# variable_list = ['Kdown', 'Kup', 'Ldown', 'Lup', 'Tsurf', 'QN', 'QF', 'QS', 'QH', 'QE', 'QHlumps', 'QElumps', 'QHresis', 'Rain', 'Irr', 'Evap', 'RO', 'TotCh', 'SurfCh', 'State', 'NWtrState', 'Drainage', 'SMD', 'FlowCh', 'AddWater', 'ROSoil', 'ROPipe', 'ROImp', 'ROVeg', 'ROWater', 'WUInt', 'WUEveTr', 'WUDecTr', 'WUGrass', 'SMDPaved', 'SMDBldgs', 'SMDEveTr', 'SMDDecTr', 'SMDGrass', 'SMDBSoil', 'StPaved', 'StBldgs', 'StEveTr', 'StDecTr', 'StGrass', 'StBSoil', 'StWater', 'Zenith', 'Azimuth', 'AlbBulk', 'Fcld', 'LAI', 'z0m', 'zdm', 'UStar', 'Lob', 'RA', 'RS', 'Fc', 'FcPhoto', 'FcRespi', 'FcMetab', 'FcTraff', 'FcBuild', 'FcPoint', 'QNSnowFr', 'QNSnow', 'AlbSnow', 'QM', 'QMFreeze', 'QMRain', 'SWE', 'MeltWater', 'MeltWStore', 'SnowCh', 'SnowRPaved', 'SnowRBldgs', 'Ts', 'T2', 'Q2', 'U10', 'RH2'] #full

variable_list = ['Tsurf', 'QN', 'QF', 'QS', 'QH', 'QE', 'QHlumps', 'QElumps', 'QHresis', 'AlbBulk', 'Fc', 'Ts', 'T2', 'Q2', 'U10', 'RH2']

cover_list = ['LCZ1', 'LCZ2', 'LCZ3', 'LCZ4', 'LCZ5', 'LCZ6', 'LCZ7', 'LCZ8', 'LCZ9', 'LCZ10', 'LCZ11', 'LCZ12', 'LCZ13', 'LCZ14', 'LCZ15', 'LCZ16', 'LCZ17', 'Paved (-)', 'Buildings (-)', 'Grass (-)', 'Deciduous trees (-)', 'Evergreen trees (-)', 'Bare soil (-)', 'Water (-)', 'Mean building height (m)', 'Mean vegetation height (m)', 'Albedo (-)', 'Height-to-width ratio (-)', 'Frontal area index buildings (-)', 'Frontal area index deciduous tree (-)', 'Frontal area index evergeen tree (-)']

try:
    for individual_split_site in split_site_list_df.index:
        individual_split_path = f'data/{individual_split_site}/output/grid'
        split_output_file = Path(individual_split_path, 'df_output_uMF_uLCu.h5')
        split_output_file.exists()
except:
    raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), split_output_file)
else:
    print(f"Output .h5 files for all runs successfully generated.")

# Intialize dataframes

# final_split_df = pd.MultiIndex(levels=[[],[],[],[]],
                       # codes=[[],[],[],[]], names=[u'grid', u'timestamp', u'latitude', u'longitude'])
 
final_split_df = pd.MultiIndex(levels=[[],[],[]],
                       codes=[[],[],[]], names=[u'timestamp', u'latitude', u'longitude'])

final_split_df = pd.DataFrame(index = final_split_df, columns = variable_list)
final_split_df = final_split_df.rename_axis(columns='var')

# converting Index dtypes so xarray converter correctly understands Index values

# grid
# final_split_df.index = final_split_df.index.set_levels(final_split_df.index.levels[0].astype('int64'), level=0)

# timestamp
final_split_df.index = final_split_df.index.set_levels(final_split_df.index.levels[0].astype('datetime64[ns]'), level=0)

# latitiude and longitude
final_split_df.index = final_split_df.index.set_levels(final_split_df.index.levels[1].astype('float64'), level=1)
final_split_df.index = final_split_df.index.set_levels(final_split_df.index.levels[2].astype('float64'), level=2)

print(final_split_df.index.dtypes)

final_split_surf_frac = pd.MultiIndex(levels=[[],[]],
                       codes=[[],[]], names=[u'latitude', u'longitude'])
                       
final_split_surf_frac = pd.DataFrame(index = final_split_surf_frac, columns = cover_list)
print(final_split_surf_frac)

split_metre_length = 1000  * split_grid_length
split_file_count = 0

# rewrite forloop to read files per variable column instead of all variables at once?
# convert to xarray at the split file level and concat as dataset instead of using pandas

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
    
    # inserting latlong as index
    split_latlon_iter = int(individual_split_df.shape[0] / len(split_grid_lat))
    split_grid_lat_iter = split_grid_lat * split_latlon_iter
    split_grid_lon_iter = split_grid_lon * split_latlon_iter
    individual_split_df.set_index([split_grid_lat_iter, split_grid_lon_iter], append = True, inplace = True)
    
    individual_split_surf_frac.set_index([split_grid_lat, split_grid_lon], append = True, inplace = True)
    
    individual_split_df.reset_index(level=0, drop = True, inplace = True)
    individual_split_surf_frac.reset_index(level=0, drop = True, inplace = True)
    
    individual_split_df.index.rename(['timestamp', 'latitude', 'longitude'], inplace = True)

    print(f'Processing output file for {individual_split_name}')

    # merging to final df
    final_split_surf_frac = pd.concat([final_split_surf_frac, individual_split_surf_frac], join = 'inner')
    final_split_df = pd.concat([final_split_df, individual_split_df], join = 'inner')
    split_file_count += 1
    
    # if split_file_count == 4: # running for the first 4 files only.
        # print(final_split_df.index)
        # print(final_split_df)
        # print(final_split_surf_frac)
        # print(final_split_surf_frac.index)
        # break 

# XArray conversion to netCDF output

output_file = 'data/consolidated_outputs/'

# hdf5 testing

print(final_split_df.index)
final_split_surf_frac.to_csv(Path(output_file, site_prefix + 'surffrac_consolidated.csv'), mode = 'w', index_label = ("latitude", "longitude"))

print(final_split_df)
final_split_df.to_hdf(Path(output_file, site_prefix + '_consolidated.h5'), key='df', mode = 'w')

final_split_ds = xr.Dataset.from_dataframe(final_split_df)
print(final_split_ds)

final_split_ds.to_netcdf(path = Path(output_file, site_prefix + '_consolidated.nc'), mode ='w')






