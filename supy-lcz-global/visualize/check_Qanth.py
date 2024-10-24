import os
os.environ['USE_PYGEOS'] = '0'
import numpy as np
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import make_axes_locatable
import xarray as xr
from atmosp import calculate as ac
import warnings
warnings.filterwarnings("ignore")

fn_dir = "./data"
fig_dir = "/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/figs"

exp_cols = ['#a6611a', '#dfc27d', '#80cdc1', '#018571']
exp_syms = ['*', '.', 'P', 'x']

def get_city_from_site_list(city: str) -> pd.Series:
    site_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
    # this should always only be a one row df!
    return site_list[site_list['sitename'] == city].iloc[0]

site_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
cities = site_list['sitename'].values
cities = ["FI-Torni"]
cities = ["US-Baltimore"]

for city in cities:

    site_info = get_city_from_site_list(city)


    # Forcing as provided by UP (Lipson et al., 2022)
    # Full period, in UTC
    fn_up_forcing = f'/home/demuzmp4/Nextcloud/data/Urban-PLUMBER_Sitedata_OpenCollection_v0.92/' \
                    f'{city}/timeseries/{city}_metforcing_v0.9.nc'
    ds_up = xr.open_dataset(fn_up_forcing)

    # Observations as provided by UP
    fn_up_obs = f'/home/demuzmp4/Nextcloud/data/Urban-PLUMBER_Sitedata_OpenCollection_v0.92/' \
                    f'{city}/timeseries/{city}_clean_observations_v0.9.nc'
    ds_obs = xr.open_dataset(fn_up_obs)


    # Forcing that drives SUPY, Full period, in LT
    # Differs for analysis period, depending on the choosen experiment

    fn_1_1b = f'{fn_dir}/{city}/output/output_1_1b.nc'
    ds_1_1b = xr.open_dataset(fn_1_1b)

    fn_1_2b = f'{fn_dir}/{city}/output/output_1_2b.nc'
    ds_1_2b = xr.open_dataset(fn_1_2b)

    fn_3_1b = f'{fn_dir}/{city}/output/output_3_1b.nc'
    ds_3_1b = xr.open_dataset(fn_3_1b)

    fn_3_2b = f'{fn_dir}/{city}/output/output_3_2b.nc'
    ds_3_2b = xr.open_dataset(fn_3_2b)

    # # Set SUPY output back to UTC => OUTPUT SHOULD ALREADY BE IN UTC - UP FORMAT!
    # utc_offset = int(site_info['local_utc_offset_hours'])
    # ds_1_1b.index = ds_1_1b.index - timedelta(hours=utc_offset)
    # ds_1_2b.index = ds_1_2b.index - timedelta(hours=utc_offset)
    # ds_3_1b.index = ds_3_1b.index - timedelta(hours=utc_offset)
    # ds_3_2b.index = ds_3_2b.index - timedelta(hours=utc_offset)

    start = site_info['time_coverage_start']
    start_ana = site_info['time_analysis_start']
    end = site_info['time_coverage_end']


    # Make a plot, for SWup, LWup, Qh, and Qle
    vars = ['Qanth']

    fig, ax = plt.subplots(len(vars),2, figsize=(15,4*len(vars)), sharex='col', gridspec_kw={'width_ratios':[3,1]})

    # Loop over the variables of interest
    for v_i, var in enumerate(vars):

        series_1_1b = ds_1_1b[var].loc[start_ana: end].squeeze()
        series_1_2b = ds_1_2b[var].loc[start_ana: end].squeeze()
        series_3_1b = ds_3_1b[var].loc[start_ana: end].squeeze()
        series_3_2b = ds_3_2b[var].loc[start_ana: end].squeeze()

        mean_1_1b = series_1_1b.groupby(series_1_1b.time.dt.hour).mean()
        mean_1_2b = series_1_2b.groupby(series_1_2b.time.dt.hour).mean()
        mean_3_1b = series_3_1b.groupby(series_3_1b.time.dt.hour).mean()
        mean_3_2b = series_3_2b.groupby(series_3_2b.time.dt.hour).mean()

        std_1_1b = series_1_1b.groupby(series_1_1b.time.dt.hour).std()
        std_1_2b = series_1_2b.groupby(series_1_2b.time.dt.hour).std()
        std_3_1b = series_3_1b.groupby(series_3_1b.time.dt.hour).std()
        std_3_2b = series_3_2b.groupby(series_3_2b.time.dt.hour).std()

        # Timeseries
        ax[0].plot(series_1_1b, label='1_1b', lw=4)
        ax[0].plot(series_1_2b, label='1_2b', lw=3)
        ax[0].plot(series_3_1b, label='3_1b', lw=2)
        ax[0].plot(series_3_2b, label='3_2b', lw=1)

        # Diurnal Cycle
        ax[1].plot(mean_1_1b.hour, mean_1_1b, label="1_1b")
        ax[1].fill_between(mean_1_1b.hour, mean_1_1b-std_1_1b, mean_1_1b+std_1_1b, alpha=0.1)

        ax[1].plot(mean_1_2b.hour, mean_1_2b, label="1_2b")
        ax[1].fill_between(mean_1_2b.hour, mean_1_2b-std_1_2b, mean_1_2b+std_1_2b, alpha=0.1)

        ax[1].plot(mean_3_1b.hour, mean_3_1b, label="3_1b")
        ax[1].fill_between(mean_3_1b.hour, mean_3_1b-std_3_1b, mean_3_1b+std_3_1b, alpha=0.1)

        ax[1].plot(mean_3_2b.hour, mean_3_2b, label="3_2b")
        ax[1].fill_between(mean_3_2b.hour, mean_3_2b-std_3_2b, mean_3_2b+std_3_2b, alpha=0.1)
        ax[1].legend()

    plt.tight_layout()
    fig_name = os.path.join(
        fig_dir,
        f"{city}_check_Qanth.png"
    )
    plt.savefig(fig_name)
    plt.close('all')
