import supy
import pandas as pd
from pathlib import Path
from datetime import timedelta

def get_city_from_site_list(city: str) -> pd.Series:
    site_list = pd.read_csv('/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/resources/sitelist_urbanplumber.csv')
    # this should always only be a one row df!
    return site_list[site_list['sitename'] == city].iloc[0]
def gen_era5_forcing(site_info):

    dir_save = Path('data', site_info['sitename'], 'input', 'era5')
    dir_save.mkdir(parents=True, exist_ok=True)

    start_date = (pd.to_datetime(site_info['time_analysis_start']) - timedelta(days=2)).strftime('%Y-%m-%d')
    end_date = (pd.to_datetime(site_info['time_coverage_end']) + timedelta(days=2)).strftime('%Y-%m-%d')

    supy.util.gen_forcing_era5(
        lat_x=float(site_info['latitude']),
        lon_x=float(site_info['longitude']),
        start=start_date,
        end=end_date,
        dir_save=dir_save,
        grid=None,
        hgt_agl_diag=100.0, # Default SUPY value.
        scale=0,
        force_download=False,
        simple_mode=True,
        pressure_level=None,
    )

def gen_era5_forcing_custom(site_info, start_date, end_date):

    ''' custom gen forcing to add some missing data'''
    dir_save = Path('data', site_info['sitename'], 'input', 'era5')
    dir_save.mkdir(parents=True, exist_ok=True)

    #start_date = (pd.to_datetime(site_info['time_analysis_start']) - timedelta(days=2)).strftime('%Y-%m-%d')
    #end_date = (pd.to_datetime(site_info['time_coverage_end']) + timedelta(days=2)).strftime('%Y-%m-%d')

    supy.util.gen_forcing_era5(
        lat_x=float(site_info['latitude']),
        lon_x=float(site_info['longitude']),
        start=start_date,
        end=end_date,
        dir_save=dir_save,
        grid=None,
        hgt_agl_diag=100.0, # Default SUPY value.
        scale=0,
        force_download=True,
        simple_mode=True,
        pressure_level=None,
    )

cities = [
    #"AU-Preston",
    # "AU-SurreyHills",
    "CA-Sunset",
    "FI-Kumpula",
    "FI-Torni",
    # "FR-Capitole",
    # "GR-HECKOR",
    # "JP-Yoyogi",
    # "KR-Jungnang",
    # "KR-Ochang",
    # "MX-Escandon",
    #"NL-Amsterdam",
    "PL-Lipowa",
    "PL-Narutowicza",
    # "SG-TelokKurau06",
    # "UK-KingsCollege",
    # "UK-Swindon",
    # "US-Baltimore",
    # "US-Minneapolis1",
    # "US-Minneapolis2",
    # "US-WestPhoenix",
]

city_times = {
    'CA-Sunset': ('2017-01-01', '2017-01-03'),
    'FI-Kumpula': ('2014-01-01', '2014-01-03'),
    'FI-Torni': ('2014-01-01', '2014-01-03'),
    'PL-Lipowa': ('2013-01-01', '2013-01-03'),
    'PL-Narutowicza': ('2013-01-01', '2013-01-03'),
}

for city in cities:


    site_info = get_city_from_site_list(city)

    #print(site_info)
    #print(site_info['time_coverage_end'])

    gen_era5_forcing(site_info)

    # # to add some missing days
    # start_date = city_times[city][0]
    # end_date = city_times[city][1]
    # gen_era5_forcing_custom(site_info, start_date=start_date, end_date=end_date)

# # For testing
# import xarray as xr
# fn = "/home/demuzmp4/data/AU-SurreyHills/input/era5/37.875S145.125E-200407-sfc.nc"
# ds = xr.open_dataset(fn)
# print(ds.time)