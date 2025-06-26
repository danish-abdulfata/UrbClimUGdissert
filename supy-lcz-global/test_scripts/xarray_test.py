import time
import pandas as pd
import numpy as np
from pathlib import Path
from pyproj import CRS
from pyproj import Transformer
import xarray as xr

split_runs_start = time.time()
split_site_list_df = pd.read_csv(Path('resources/GreaterKL-2017_Y1_M2sp_3sf_R1_splitlist.csv'))
split_site_list_df.index.name = 'sitename'
number_of_runs = 3
split_grid_length = 5
split_grid_area = split_grid_length**2
split_run_count = 0
site_prefix = "GreaterKL-2017_Y1_M2sp_3sf_R1"

output_file = './data/consolidated_outputs/'

# hdf5 testing

final_split_df = pd.read_hdf(Path(output_file, site_prefix + '_consolidated.h5'))

# final_split_df.to_xarray(Path(output_file, site_prefix + '_consolidated.nc'), key='df', mode = 'w')

final_split_ds = xr.Dataset.from_dataframe(final_split_df, sparse=True)
final_split_ds.to_netcdf(path = Path(output_file, site_prefix + '_consolidated.nc'), mode ='w')

# final_split_ds = xr.open_dataset(Path(output_file, site_prefix + '_consolidated.h5'), engine = "h5netcdf", chunks="auto", group = "df", phony_dims="access")
# print(final_split_ds)
