import time
import pandas as pd
import numpy as np
from pathlib import Path
from pyproj import CRS
from pyproj import Transformer
import xarray as xr
from runner.runner import main as run_runner
############################# Testing for run_split_models.py, 2nd part.

split_runs_start = time.time()
split_site_list_df = pd.read_csv(Path('resources/KL-KualaLumpur-2017_1Msp_1_splitlist.csv'))
split_site_list_df.index.name = 'sitename'
number_of_runs = 3
split_grid_length = 5
split_grid_area = split_grid_length**2
split_run_count = 0
site_prefix = "KL-KualaLumpur-2017_1month_runnertest"

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

# all variables = ['Kdown', 'Kup', 'Ldown', 'Lup', 'Tsurf', 'QN', 'QF', 'QS', 'QH', 'QE', 'QHlumps', 'QElumps', 'QHresis', 'Rain', 'Irr', 'Evap', 'RO', 'TotCh', 'SurfCh', 'State', 'NWtrState', 'Drainage', 'SMD', 'FlowCh', 'AddWater', 'ROSoil', 'ROPipe', 'ROImp', 'ROVeg', 'ROWater', 'WUInt', 'WUEveTr', 'WUDecTr', 'WUGrass', 'SMDPaved', 'SMDBldgs', 'SMDEveTr', 'SMDDecTr', 'SMDGrass', 'SMDBSoil', 'StPaved', 'StBldgs', 'StEveTr', 'StDecTr', 'StGrass', 'StBSoil', 'StWater', 'Zenith', 'Azimuth', 'AlbBulk', 'Fcld', 'LAI', 'z0m', 'zdm', 'UStar', 'Lob', 'RA', 'RS', 'Fc', 'FcPhoto', 'FcRespi', 'FcMetab', 'FcTraff', 'FcBuild', 'FcPoint', 'QNSnowFr', 'QNSnow', 'AlbSnow', 'QM', 'QMFreeze', 'QMRain', 'SWE', 'MeltWater', 'MeltWStore', 'SnowCh', 'SnowRPaved', 'SnowRBldgs', 'Ts', 'T2', 'Q2', 'U10', 'RH2']

variable_list = ['Kdown', 'Kup', 'Ldown', 'Lup', 'Tsurf', 'QN', 'QF', 'QS', 'QH', 'QE', 'QHlumps', 'QElumps', 'QHresis', 'Rain', 'Irr', 'Evap', 'RO', 'TotCh', 'SurfCh', 'State', 'NWtrState', 'Drainage', 'SMD', 'FlowCh', 'AddWater', 'ROSoil', 'ROPipe', 'ROImp', 'ROVeg', 'ROWater', 'WUInt', 'WUEveTr', 'WUDecTr', 'WUGrass', 'SMDPaved', 'SMDBldgs', 'SMDEveTr', 'SMDDecTr', 'SMDGrass', 'SMDBSoil', 'StPaved', 'StBldgs', 'StEveTr', 'StDecTr', 'StGrass', 'StBSoil', 'StWater', 'Zenith', 'Azimuth', 'AlbBulk', 'Fcld', 'LAI', 'z0m', 'zdm', 'UStar', 'Lob', 'RA', 'RS', 'Fc', 'FcPhoto', 'FcRespi', 'FcMetab', 'FcTraff', 'FcBuild', 'FcPoint', 'QNSnowFr', 'QNSnow', 'AlbSnow', 'QM', 'QMFreeze', 'QMRain', 'SWE', 'MeltWater', 'MeltWStore', 'SnowCh', 'SnowRPaved', 'SnowRBldgs', 'Ts', 'T2', 'Q2', 'U10', 'RH2']

cover_list = ['LCZ1', 'LCZ2', 'LCZ3', 'LCZ4', 'LCZ5', 'LCZ6', 'LCZ7', 'LCZ8', 'LCZ9', 'LCZ10', 'LCZ11', 'LCZ12', 'LCZ13', 'LCZ14', 'LCZ15', 'LCZ16', 'LCZ17', 'Paved (-)', 'Buildings (-)', 'Grass (-)', 'Deciduous trees (-)', 'Evergreen trees (-)', 'Bare soil (-)', 'Water (-)', 'Mean building height (m)', 'Mean vegetation height (m)', 'Albedo (-)', 'Height-to-width ratio (-)', 'Frontal area index buildings (-)', 'Frontal area index deciduous tree (-)', 'Frontal area index evergeen tree (-)']

# Intialize dataframes

final_split_df = pd.MultiIndex(levels=[[],[],[],[]],
                       codes=[[],[],[],[]], names=[u'grid', u'timestamp', u'latitude', u'longitude'])
                       
final_split_df = pd.DataFrame(index = final_split_df, columns = variable_list)
final_split_df = final_split_df.rename_axis(columns='var')

# converting Index dtypes so xarray converter correctly understands Index values

# grid
final_split_df.index = final_split_df.index.set_levels(final_split_df.index.levels[0].astype('int64'), level=0)

# timestamp
final_split_df.index = final_split_df.index.set_levels(final_split_df.index.levels[1].astype('datetime64[ns]'), level=1)

# latitiude and longitude
final_split_df.index = final_split_df.index.set_levels(final_split_df.index.levels[2].astype('float64'), level=2)
final_split_df.index = final_split_df.index.set_levels(final_split_df.index.levels[3].astype('float64'), level=3)

final_split_df_print = final_split_df.index.dtypes
print(final_split_df_print)

# raise SystemExit()

final_split_surf_frac = pd.DataFrame(columns = cover_list)
final_split_surf_frac.index.name = 'grid'
#print(final_split_df)


split_metre_length = 1000  * split_grid_length
split_file_count = 0

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
    
    individual_split_surf_frac.insert(0, 'latitude', split_grid_lat)
    individual_split_surf_frac.insert(1, 'longitude', split_grid_lon)
        
    # changing grid numbers
    file_grid_number = individual_split_df.index.levels[0]
    modified_grid_numbers = file_grid_number + (split_file_count * split_grid_area)
    grid_number_dict = dict(list(zip(file_grid_number.to_list(), modified_grid_numbers.to_list())))
        
    individual_split_df.rename(grid_number_dict, level = 'grid', inplace = True)
    individual_split_surf_frac.rename(index = grid_number_dict, inplace = True)
    
    individual_split_df.index.rename(['grid', 'timestamp', 'latitude', 'longitude'], inplace = True)

    print(f'Processing output file for {individual_split_name}')
    # merging to final df
    final_split_surf_frac = pd.concat([final_split_surf_frac, individual_split_surf_frac], join = 'inner')
    final_split_df = pd.concat([final_split_df, individual_split_df], join = 'inner')
    split_file_count += 1
    
    if split_file_count == 4: # running for the first 4 files only.
        print(final_split_df.index)
        print(final_split_df)
        print(final_split_surf_frac)
        print(final_split_surf_frac.index)
        break
        
# XArray conversion to netCDF output

output_file = f'data/consolidated_outputs/'
final_split_df_xr = final_split_df.to_xarray()
print(final_split_df_xr)
final_split_df_xr.to_netcdf(path = Path(output_file, site_prefix + '_consolidated.nc'), mode ='w')

final_split_surf_frac_xr = final_split_surf_frac.to_xarray()
final_split_surf_frac_xr.to_netcdf(path = Path(output_file, site_prefix + '_surf_frac.nc'), mode ='w')

# final_split_df.to_xarray()
# final_split_surf_frac.to_xarray()



