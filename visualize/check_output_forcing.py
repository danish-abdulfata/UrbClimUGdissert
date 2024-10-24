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
cities = ['FI-Torni']
cities = ["US-Baltimore"]

def resample_forcing(ds, timestep):

    freq = timestep/60 #in min
    ds_r = ds.resample(f'{freq}min').mean()
    ds_r['rain'] = ds.rain.resample(f'{freq}min').sum()

    return ds_r

for city in cities:

    site_info = get_city_from_site_list(city)
    timestep = site_info['timestep_interval_seconds']
    if timestep == 1800:
        steps = 6
    else:
        steps=12

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

    fn_1_1b = f'{fn_dir}/{city}/output/df_final_forcing_1_1b.h5'
    ds_1_1b = pd.read_hdf(fn_1_1b, parse_dates=True)
    #ds_1_1b_r = resample_forcing(ds_1_1b, timestep)
    ds_1_1b = ds_1_1b.iloc[::steps,:]

    fn_1_2b = f'{fn_dir}/{city}/output/df_final_forcing_1_2b.h5'
    ds_1_2b = pd.read_hdf(fn_1_2b, parse_dates=True)
    ds_1_2b = ds_1_2b.iloc[::steps, :]

    fn_3_1b = f'{fn_dir}/{city}/output/df_final_forcing_3_1b.h5'
    ds_3_1b = pd.read_hdf(fn_3_1b, parse_dates=True)
    ds_3_1b = ds_3_1b.iloc[::steps, :]

    fn_3_2b = f'{fn_dir}/{city}/output/df_final_forcing_3_2b.h5'
    ds_3_2b = pd.read_hdf(fn_3_2b, parse_dates=True)
    ds_3_2b = ds_3_2b.iloc[::steps, :]

    # Set SUPY output back to UTC
    utc_offset = int(site_info['local_utc_offset_hours'])
    ds_1_1b.index = ds_1_1b.index - timedelta(hours=utc_offset)
    ds_1_2b.index = ds_1_2b.index - timedelta(hours=utc_offset)
    ds_3_1b.index = ds_3_1b.index - timedelta(hours=utc_offset)
    ds_3_2b.index = ds_3_2b.index - timedelta(hours=utc_offset)

    start = site_info['time_coverage_start']
    start_ana = site_info['time_analysis_start']
    end = site_info['time_coverage_end']


    # Make a plot for forcing - split in spin-up and analysis period
    fig, ax = plt.subplots(
        2,7,
        figsize=(20,5)
    )

    # SWdown
    ax_i = 0; up_var = 'SWdown'; supy_var = "kdown"
    for tt in [0,1]:
        if tt == 0:
            st = start
            en = start_ana
            yax = 0
        else:
            st = start_ana
            en = end
            yax = 1

        series_up = ds_up[up_var].sel(time=slice(st,en)).squeeze().to_pandas()
        series_1_1b = ds_1_1b[supy_var].loc[st:en]
        series_1_2b = ds_1_2b[supy_var].loc[st:en]
        series_3_1b = ds_3_1b[supy_var].loc[st:en]
        series_3_2b = ds_3_2b[supy_var].loc[st:en]

        ax[yax, ax_i].scatter(series_up, series_3_1b, s=3, label="3_1b", color=exp_cols[0], marker=exp_syms[0])
        ax[yax, ax_i].scatter(series_up, series_3_2b, s=1, label="3_2b", color=exp_cols[1], marker=exp_syms[1])
        ax[yax, ax_i].scatter(series_up, series_1_1b, s=3, label="1_1b", color=exp_cols[2], marker=exp_syms[2])
        ax[yax, ax_i].scatter(series_up, series_1_2b, s=1, label="1_2b", color=exp_cols[3], marker=exp_syms[3])
    ax[0, ax_i].set_title("SWdown")

    # LWdown
    ax_i = 1;
    up_var = 'LWdown';
    supy_var = "ldown"
    for tt in [0, 1]:
        if tt == 0:
            st = start
            en = start_ana
            yax = 0
        else:
            st = start_ana
            en = end
            yax = 1

        series_up = ds_up[up_var].sel(time=slice(st, en)).squeeze().to_pandas()
        series_1_1b = ds_1_1b[supy_var].loc[st:en]
        series_1_2b = ds_1_2b[supy_var].loc[st:en]
        series_3_1b = ds_3_1b[supy_var].loc[st:en]
        series_3_2b = ds_3_2b[supy_var].loc[st:en]

        ax[yax, ax_i].scatter(series_up, series_3_1b, s=3, label="3_1b", color=exp_cols[0], marker=exp_syms[0])
        ax[yax, ax_i].scatter(series_up, series_3_2b, s=1, label="3_2b", color=exp_cols[1], marker=exp_syms[1])
        ax[yax, ax_i].scatter(series_up, series_1_1b, s=3, label="1_1b", color=exp_cols[2], marker=exp_syms[2])
        ax[yax, ax_i].scatter(series_up, series_1_2b, s=1, label="1_2b", color=exp_cols[3], marker=exp_syms[3])
    ax[0, ax_i].set_title("LWdown")

    # Pressure
    ax_i = 2;
    up_var = 'PSurf';
    supy_var = "pres"
    for tt in [0, 1]:
        if tt == 0:
            st = start
            en = start_ana
            yax = 0
        else:
            st = start_ana
            en = end
            yax = 1

        series_up = ds_up[up_var].sel(time=slice(st, en)).squeeze().to_pandas()
        series_1_1b = ds_1_1b[supy_var].loc[st:en]*1000
        series_1_2b = ds_1_2b[supy_var].loc[st:en]*1000
        series_3_1b = ds_3_1b[supy_var].loc[st:en]*1000
        series_3_2b = ds_3_2b[supy_var].loc[st:en]*1000

        ax[yax, ax_i].scatter(series_up, series_3_1b, s=3, label="3_1b", color=exp_cols[0], marker=exp_syms[0])
        ax[yax, ax_i].scatter(series_up, series_3_2b, s=1, label="3_2b", color=exp_cols[1], marker=exp_syms[1])
        ax[yax, ax_i].scatter(series_up, series_1_1b, s=3, label="1_1b", color=exp_cols[2], marker=exp_syms[2])
        ax[yax, ax_i].scatter(series_up, series_1_2b, s=1, label="1_2b", color=exp_cols[3], marker=exp_syms[3])
    ax[0, ax_i].set_title("Pressure")

    # Wind
    ax_i = 3;
    up_var = 'Wind_N' + 'Wind_E'
    supy_var = "U"
    for tt in [0, 1]:
        if tt == 0:
            st = start
            en = start_ana
            yax = 0
        else:
            st = start_ana
            en = end
            yax = 1

        series_up = ((ds_up['Wind_N'].sel(time=slice(st, en)).squeeze().to_pandas())**2 + \
                        (ds_up['Wind_E'].sel(time=slice(st, en)).squeeze().to_pandas()) ** 2) **0.5
        series_1_1b = ds_1_1b[supy_var].loc[st:en]
        series_1_2b = ds_1_2b[supy_var].loc[st:en]
        series_3_1b = ds_3_1b[supy_var].loc[st:en]
        series_3_2b = ds_3_2b[supy_var].loc[st:en]

        ax[yax, ax_i].scatter(series_up, series_3_1b, s=3, label="3_1b", color=exp_cols[0], marker=exp_syms[0])
        ax[yax, ax_i].scatter(series_up, series_3_2b, s=1, label="3_2b", color=exp_cols[1], marker=exp_syms[1])
        ax[yax, ax_i].scatter(series_up, series_1_1b, s=3, label="1_1b", color=exp_cols[2], marker=exp_syms[2])
        ax[yax, ax_i].scatter(series_up, series_1_2b, s=1, label="1_2b", color=exp_cols[3], marker=exp_syms[3])
    ax[0, ax_i].set_title("U")

    # Precipitation
    ax_i = 4;
    up_var = 'Rainf' + 'Snowf'
    supy_var = "rain"
    for tt in [0, 1]:
        if tt == 0:
            st = start
            en = start_ana
            yax = 0
        else:
            st = start_ana
            en = end
            yax = 1

        series_up = ds_up['Rainf'].sel(time=slice(st, en)).squeeze().to_pandas() + \
                    ds_up['Snowf'].sel(time=slice(st, en)).squeeze().to_pandas()
        series_1_1b = ds_1_1b[supy_var].loc[st:en] / 1800
        series_1_2b = ds_1_2b[supy_var].loc[st:en] / 1800
        series_3_1b = ds_3_1b[supy_var].loc[st:en] / 1800
        series_3_2b = ds_3_2b[supy_var].loc[st:en] / 1800

        ax[yax, ax_i].scatter(series_up, series_3_1b, s=3, label="3_1b", color=exp_cols[0], marker=exp_syms[0])
        ax[yax, ax_i].scatter(series_up, series_3_2b, s=1, label="3_2b", color=exp_cols[1], marker=exp_syms[1])
        ax[yax, ax_i].scatter(series_up, series_1_1b, s=3, label="1_1b", color=exp_cols[2], marker=exp_syms[2])
        ax[yax, ax_i].scatter(series_up, series_1_2b, s=1, label="1_2b", color=exp_cols[3], marker=exp_syms[3])
    ax[0, ax_i].set_title("Precipitation")

    # Temperature
    ax_i = 5;
    up_var = 'Tair'
    supy_var = "Tair"
    for tt in [0, 1]:
        if tt == 0:
            st = start
            en = start_ana
            yax = 0
        else:
            st = start_ana
            en = end
            yax = 1

        series_up = ds_up['Tair'].sel(time=slice(st, en)).squeeze().to_pandas()

        series_1_1b = ds_1_1b[supy_var].loc[st:en] + 273.15
        series_1_2b = ds_1_2b[supy_var].loc[st:en] + 273.15
        series_3_1b = ds_3_1b[supy_var].loc[st:en] + 273.15
        series_3_2b = ds_3_2b[supy_var].loc[st:en] + 273.15

        ax[yax, ax_i].scatter(series_up, series_3_1b, s=3, label="3_1b", color=exp_cols[0], marker=exp_syms[0])
        ax[yax, ax_i].scatter(series_up, series_3_2b, s=1, label="3_2b", color=exp_cols[1], marker=exp_syms[1])
        ax[yax, ax_i].scatter(series_up, series_1_1b, s=3, label="1_1b", color=exp_cols[2], marker=exp_syms[2])
        ax[yax, ax_i].scatter(series_up, series_1_2b, s=1, label="1_2b", color=exp_cols[3], marker=exp_syms[3])
    ax[0, ax_i].set_title("Temperature")


    # Specific humidity
    ax_i = 6;
    up_var = 'Qair'
    supy_var = "RH"
    for tt in [0, 1]:
        if tt == 0:
            st = start
            en = start_ana
            yax = 0
        else:
            st = start_ana
            en = end
            yax = 1

        series_up = ds_up['Qair'].sel(time=slice(st, en)).squeeze().to_pandas()

        series_1_1b_rh = ds_1_1b['RH'].loc[st:en] # %
        series_1_1b_p = ds_1_1b['pres'].loc[st:en] * 1000 # Pa
        series_1_1b_t = ds_1_1b['Tair'].loc[st:en] + 273.15 # K
        series_1_1b_q_z = ac("qv", RH=series_1_1b_rh, p=series_1_1b_p, T=series_1_1b_t, RH_unit="percent")

        series_1_2b_rh = ds_1_2b['RH'].loc[st:en] # %
        series_1_2b_p = ds_1_2b['pres'].loc[st:en] * 1000 # Pa
        series_1_2b_t = ds_1_2b['Tair'].loc[st:en] + 273.15 # K
        series_1_2b_q_z = ac("qv", RH=series_1_2b_rh, p=series_1_2b_p, T=series_1_2b_t, RH_unit="percent")

        series_3_1b_rh = ds_3_1b['RH'].loc[st:en] # %
        series_3_1b_p = ds_3_1b['pres'].loc[st:en] * 1000 # Pa
        series_3_1b_t = ds_3_1b['Tair'].loc[st:en] + 273.15 # K
        series_3_1b_q_z = ac("qv", RH=series_3_1b_rh, p=series_3_1b_p, T=series_3_1b_t, RH_unit="percent")

        series_3_2b_rh = ds_3_2b['RH'].loc[st:en] # %
        series_3_2b_p = ds_3_2b['pres'].loc[st:en] * 1000 # Pa
        series_3_2b_t = ds_3_2b['Tair'].loc[st:en] + 273.15 # K
        series_3_2b_q_z = ac("qv", RH=series_3_2b_rh, p=series_3_2b_p, T=series_3_2b_t, RH_unit="percent")


        ax[yax, ax_i].scatter(series_up, series_3_1b_q_z, s=3, label="3_1b", color=exp_cols[0], marker=exp_syms[0])
        ax[yax, ax_i].scatter(series_up, series_3_2b_q_z, s=1, label="3_2b", color=exp_cols[1], marker=exp_syms[1])
        ax[yax, ax_i].scatter(series_up, series_1_1b_q_z, s=3, label="1_1b", color=exp_cols[2], marker=exp_syms[2])
        ax[yax, ax_i].scatter(series_up, series_1_2b_q_z, s=1, label="1_2b", color=exp_cols[3], marker=exp_syms[3])
    ax[0, ax_i].set_title("Qair")

    plt.tight_layout()
    fig_name = os.path.join(
        fig_dir,
        f"{city}_check_output_forcing.png"
    )
    plt.savefig(fig_name)
    plt.close('all')