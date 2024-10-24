import pandas as pd
import numpy as np
import xarray as xr
import os

print(Path.cwd())
projpath = '/home/demuzmp4/Nextcloud/data/Urban-PLUMBER_Sitedata_OpenCollection_v0.92'

# add sites to list as required
sitelist = ['AU-Preston','AU-SurreyHills','CA-Sunset','FI-Kumpula','FI-Torni','FR-Capitole',
            'GR-HECKOR','JP-Yoyogi','KR-Jungnang','KR-Ochang','MX-Escandon','NL-Amsterdam',
            'PL-Lipowa','PL-Narutowicza','SG-TelokKurau06','UK-KingsCollege','UK-Swindon',
            'US-Baltimore','US-Minneapolis1','US-Minneapolis2','US-WestPhoenix']


# Initialize dataframe to store data in
df = pd.DataFrame(
    index=sitelist,
    columns= [
        'latitude',
        'longitude',
        'measurement_height_above_ground',
        'surface_cover_radius',
        'time_coverage_start',
        'time_coverage_end',
        'time_analysis_start',
        'timestep_interval_seconds',
    ]
)
df.index.name = 'sitename'

# Dict for the radius, not available within the files??
dict_radius = {
    'AU-Preston': 500,
    'AU-SurreyHills': 500,
    'CA-Sunset': 'fpm',
    'FI-Kumpula': 1000,
    'FI-Torni': 1000,
    'FR-Capitole': 500,
    'GR-HECKOR': 'fpm',
    'JP-Yoyogi': 500,
    'KR-Jungnang': 500,
    'KR-Ochang': 500,
    'MX-Escandon': 'fpm',
    'NL-Amsterdam': 500,
    'PL-Lipowa': 'fpm',
    'PL-Narutowicza': 500,
    'SG-TelokKurau06': 1000,
    'UK-KingsCollege': 'fpm',
    'UK-Swindon': 500,
    'US-Baltimore': 1000,
    'US-Minneapolis1': 'fpm',
    'US-Minneapolis2': 'fpm',
    'US-WestPhoenix': 'fpm',
}

for sitename in sitelist:

    #sitename = "AU-Preston"

    # Read the forcing file
    vif = 0.9
    path_forcing = f'{projpath}/{sitename}/timeseries/{sitename}_metforcing_v{vif}.nc'
    ds = xr.open_dataset(path_forcing)

    # Read site data
    vis = 1
    path_sitedata = f'{projpath}/{sitename}/{sitename}_sitedata_v{vis}.csv'
    sitedata_full = pd.read_csv(path_sitedata, index_col=1, delimiter=',')
    sitedata      = pd.to_numeric(sitedata_full['value'])

    # Fill the dataframe
    df.loc[sitename, 'latitude'] = sitedata['latitude']
    df.loc[sitename, 'longitude'] = sitedata['longitude']
    df.loc[sitename, 'measurement_height_above_ground'] = sitedata['measurement_height_above_ground']
    df.loc[sitename, 'surface_cover_radius'] = dict_radius[sitename]
    df.loc[sitename, 'time_coverage_start'] = ds.attrs['time_coverage_start']
    df.loc[sitename, 'time_coverage_end'] = ds.attrs['time_coverage_end']
    df.loc[sitename, 'time_analysis_start'] = ds.attrs['time_analysis_start']
    df.loc[sitename, 'timestep_interval_seconds'] = ds.attrs['timestep_interval_seconds']

    # Also copy site metadata for future use in experiments
    path_input = f"/home/demuzmp4/Nextcloud/scripts/supy-lcz/data/{sitename}/input"
    dst_path_sitedata = f"{path_input}/{path_sitedata.split('/')[-1]}"
    shutil.copy2(path_sitedata, dst_path_sitedata)

# Save to file
ofile = "/home/demuzmp4/Nextcloud/scripts/supy-lcz/resources/sitelist_urbanplumber.csv"
df.to_csv(ofile)