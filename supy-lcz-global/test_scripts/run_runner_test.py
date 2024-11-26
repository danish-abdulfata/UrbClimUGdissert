import time
import pandas as pd
from pathlib import Path
from runner.runner import main as run_runner
import test_scripts.structure_grid_output as grid_out
############################# Testing for run_split_models.py, 2nd part.

split_runs_start = time.time()
site_list_df = pd.read_csv(Path(f'resources/KL-KualaLumpur-2016_splitlist.csv'))
site_list_df.index.name = 'sitename'
number_of_runs = 3
split_grid_length = 5
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

for individual_split_site in site_list_df.index:
    individual_split_name = split_site_df.iloc[individual_split_site, 0]
    individual_split_lat = float(site_list_df.iloc[individual_split_site, 1])
    individual_split_lon = float(site_list_df.iloc[individual_split_site, 2])
    individual_split_path = f'data/{individual_split_name}/output/grid'
    grid_out.convert_h5_to_netcdf(individual_split_path + '/df_output_uMF_uLCu.h5', 1000, individual_split_lat, individual_split_lon)
    split_run_count += 1
    hdf_file = pd.read_hdf(individual_split_path + '/df_output_uMF_uLCu_latlon.nc')
    print(hdf_file)
    
    print(f"=======> {individual_split_site} output conversion complete, #{split_run_count} out of #{number_of_runs} for {site_prefix} <========")