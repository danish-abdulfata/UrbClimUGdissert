import time
import pandas as pd
from pathlib import Path
from pyproj import CRS
from pyproj import Transformer
from runner.runner import main as run_runner
############################# Testing for run_split_models.py, 2nd part.

split_runs_start = time.time()
site_list_df = pd.read_csv(Path('resources/KL-KualaLumpur-2017_1Msp_1_splitlist.csv'))
site_list_df.index.name = 'sitename'
number_of_runs = 3
split_grid_length = 5
split_grid_area = split_grid_length**2
split_run_count = 0
site_prefix = "KL-KualaLumpur-2016"

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
split_file_count = 1
model_run = 'KL-KualaLumpur-2017_1Msp_1_s1'
test_out_df = pd.read_hdf(f'data/{model_run}/output/grid/df_output_uMF_uLCu.h5')
print(test_out_df)
# file_grid_number = test_out_df.index.levels[0]
# modified_grid_numbers = file_grid_number + (split_file_count * split_grid_area)
# grid_number_dict = dict(list(zip(file_grid_number.to_list(), modified_grid_numbers.to_list())))
# print(grid_number_dict)
# test_out_df = test_out_df.rename(grid_number_dict, axis = 0, level = 'grid')
# print(test_out_df)

# defining list for all variables

# all variables = ['Kdown', 'Kup', 'Ldown', 'Lup', 'Tsurf', 'QN', 'QF', 'QS', 'QH', 'QE', 'QHlumps', 'QElumps', 'QHresis', 'Rain', 'Irr', 'Evap', 'RO', 'TotCh', 'SurfCh', 'State', 'NWtrState', 'Drainage', 'SMD', 'FlowCh', 'AddWater', 'ROSoil', 'ROPipe', 'ROImp', 'ROVeg', 'ROWater', 'WUInt', 'WUEveTr', 'WUDecTr', 'WUGrass', 'SMDPaved', 'SMDBldgs', 'SMDEveTr', 'SMDDecTr', 'SMDGrass', 'SMDBSoil', 'StPaved', 'StBldgs', 'StEveTr', 'StDecTr', 'StGrass', 'StBSoil', 'StWater', 'Zenith', 'Azimuth', 'AlbBulk', 'Fcld', 'LAI', 'z0m', 'zdm', 'UStar', 'Lob', 'RA', 'RS', 'Fc', 'FcPhoto', 'FcRespi', 'FcMetab', 'FcTraff', 'FcBuild', 'FcPoint', 'QNSnowFr', 'QNSnow', 'AlbSnow', 'QM', 'QMFreeze', 'QMRain', 'SWE', 'MeltWater', 'MeltWStore', 'SnowCh', 'SnowRPaved', 'SnowRBldgs', 'Ts', 'T2', 'Q2', 'U10', 'RH2']

variable_list = ['Kdown', 'Kup', 'Ldown', 'Lup', 'Tsurf', 'QN', 'QF', 'QS', 'QH', 'QE', 'QHlumps', 'QElumps', 'QHresis', 'Rain', 'Irr', 'Evap', 'RO', 'TotCh', 'SurfCh', 'State', 'NWtrState', 'Drainage', 'SMD', 'FlowCh', 'AddWater', 'ROSoil', 'ROPipe', 'ROImp', 'ROVeg', 'ROWater', 'WUInt', 'WUEveTr', 'WUDecTr', 'WUGrass', 'SMDPaved', 'SMDBldgs', 'SMDEveTr', 'SMDDecTr', 'SMDGrass', 'SMDBSoil', 'StPaved', 'StBldgs', 'StEveTr', 'StDecTr', 'StGrass', 'StBSoil', 'StWater', 'Zenith', 'Azimuth', 'AlbBulk', 'Fcld', 'LAI', 'z0m', 'zdm', 'UStar', 'Lob', 'RA', 'RS', 'Fc', 'FcPhoto', 'FcRespi', 'FcMetab', 'FcTraff', 'FcBuild', 'FcPoint', 'QNSnowFr', 'QNSnow', 'AlbSnow', 'QM', 'QMFreeze', 'QMRain', 'SWE', 'MeltWater', 'MeltWStore', 'SnowCh', 'SnowRPaved', 'SnowRBldgs', 'Ts', 'T2', 'Q2', 'U10', 'RH2']

# final_split_df = # see tmrw

final_split_df = pd.MultiIndex(levels=[[],[]],
                       codes=[[],[]], names=[u'grid', u'timestamp',])
                       
final_split_df = pd.DataFrame(index = final_split_df, columns = variable_list)
final_split_df = final_split_df.rename_axis(columns='var')

# use .concat() and join="inner", so that only the previously selected columns are added.
final_split_df = pd.concat([final_split_df, test_out_df]) 
print(final_split_df)
crs_dict = {
            'proj': 'utm',
            'zone': int(np.round((183 + site_midpoint_lon) / 6)),
            'south': site_midpoint_lat < 0,
        }

crs = CRS.from_dict(crs_dict)
site_list_df.index[model_run, 
    for individual_split_site in split_site_list_df.index:
        individual_split_name = split_site_list_df.iloc[individual_split_site, 0]
        individual_split_path = f'data/{individual_split_name}/output/grid'
        split_output_file = individual_split_path / 'df_output_uMF_uLCu.h5'

# convert latlong to UTM for consistency / ease of calculations
to_utm = Transformer.from_crs(crs_from='EPSG:4326', crs_to=crs)
split_midpoint_x, split_midpoint_y = to_utm.transform(xx=site_midpoint_lat, yy=site_midpoint_lon)

# identify site boundaries
split_metre_length = 1000  * split_grid_length

grid_y_max = split_midpoint_y + (split_metre_length / 2)
grid_y_min = split_y_max - (split_metre_length)
grid_x_max = split_midpoint_x + (split_metre_length / 2)
grid_x_min = split_x_max - (split_metre_length)

# +1 to account for the additional sample at the start, [1:] to remove before meshing.
grid_midpoint_x = np.linspace(grid_x_min, grid_x_max, split_grid_length + 1, endpoint = False)[1:]
grid_midpoint_y = np.linspace(grid_y_min, grid_y_max, split_grid_length + 1, endpoint = False)[1:]

# converting back to latlong
from_utm = Transformer.from_crs(crs_from=crs, crs_to='EPSG:4326')
grid_midpoint_lat, grid_midpoint_lon = from_utm.transform(xx=grid_midpoint_x, yy=grid_midpoint_y)

# repeat latlong to form a 1d grid
split_grid_xx, split_grid_yy = np.meshgrid(grid_midpoint_lat, grid_midpoint_lon)

split_grid_lat_list = np.ndarray.flatten(split_grid_xx.tolist())
split_grid_lon_list = np.ndarray.flatten(split_grid_yy.tolist())


# final for loop to copy into run_split_models

# for individual_split_site in site_list_df.index:
    # if split_file_count < 5:
        # split_file_count += 1
        # individual_split_name = split_site_df.iloc[individual_split_site, 0]
        # individual_split_path = f'data/{individual_split_name}/output/grid'
        # out_split_df = pd.read_hdf(individual_split_path / 'df_output_uMF_uLCu.h5')
        
        # Relabeling grid
# d')
        # Merging files
        # final_split_df = 
        
        # print(f"=======> {individual_split_site} output conversion complete, #{split_run_count} out of #{number_of_runs} for {site_prefix} <========")
    # else 
    # print(f"Testing complete for merging {split_run_count} of files")
    # print(out_df_merged)
    
    