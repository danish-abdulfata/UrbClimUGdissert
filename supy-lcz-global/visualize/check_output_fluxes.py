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

# Set version that is being tested, referring to github pull request
gh_pr = "sitespecific_fai"


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

cities = ['AU-Preston']
#cities = ['FI-Torni']
#cities = ["US-Baltimore"]
#cities = ["US-WestPhoenix"]

for city in cities:

    site_info = get_city_from_site_list(city)


    # Forcing as provided by UP (Lipson et al., 2022)
    # Full period, in UTC
    fn_up_forcing = f'/home/demuzmp4/Nextcloud/data/Urban-PLUMBER_FullCollection_v1/' \
                    f'{city}/timeseries/{city}_metforcing_v1.nc'
    ds_up = xr.open_dataset(fn_up_forcing)

    # Observations as provided by UP
    fn_up_obs = f'/home/demuzmp4/Nextcloud/data/Urban-PLUMBER_FullCollection_v1/' \
                    f'{city}/timeseries/{city}_clean_observations_v1.nc'
    ds_obs = xr.open_dataset(fn_up_obs)


    # Forcing that drives SUPY, Full period, in LT
    # Differs for analysis period, depending on the choosen experiment

    fn_sMF_sLC = f'{fn_dir}/{city}/output/buffer/output_sMF_sLC.nc'
    ds_sMF_sLC = xr.open_dataset(fn_sMF_sLC)

    fn_sMF_uLCu = f'{fn_dir}/{city}/output/buffer/output_sMF_uLCu.nc'
    ds_sMF_uLCu = xr.open_dataset(fn_sMF_uLCu)

    fn_uMF_sLC = f'{fn_dir}/{city}/output/buffer/output_uMF_sLC.nc'
    ds_uMF_sLC = xr.open_dataset(fn_uMF_sLC)

    fn_uMF_uLCu = f'{fn_dir}/{city}/output/buffer/output_uMF_uLCu.nc'
    ds_uMF_uLCu = xr.open_dataset(fn_uMF_uLCu)

    # # Set SUPY output back to UTC => OUTPUT SHOULD ALREADY BE IN UTC - UP FORMAT!
    # utc_offset = int(site_info['local_utc_offset_hours'])
    # ds_sMF_sLC.index = ds_sMF_sLC.index - timedelta(hours=utc_offset)
    # ds_sMF_uLCu.index = ds_sMF_uLCu.index - timedelta(hours=utc_offset)
    # ds_uMF_sLC.index = ds_uMF_sLC.index - timedelta(hours=utc_offset)
    # ds_uMF_uLCu.index = ds_uMF_uLCu.index - timedelta(hours=utc_offset)

    start = site_info['time_coverage_start']
    start_ana = site_info['time_analysis_start']
    end = site_info['time_coverage_end']


    # Make a plot, for SWup, LWup, Qh, and Qle
    vars = ['SWup', 'LWup', 'Qh', 'Qle']

    fig, ax = plt.subplots(4,2, figsize=(15,15), sharex='col', gridspec_kw={'width_ratios':[3,1]})

    # Loop over the variables of interest
    for v_i, var in enumerate(vars):

        series_up = ds_obs[var].sel(time=slice(start_ana, end)).squeeze().to_pandas()
        series_sMF_sLC = ds_sMF_sLC[var].loc[start_ana: end].squeeze()
        series_sMF_uLCu = ds_sMF_uLCu[var].loc[start_ana: end].squeeze()
        series_uMF_sLC = ds_uMF_sLC[var].loc[start_ana: end].squeeze()
        series_uMF_uLCu = ds_uMF_uLCu[var].loc[start_ana: end].squeeze()

        diff_sMF_sLC = series_sMF_sLC - series_up
        mae_diff_sMF_sLC = np.round(diff_sMF_sLC.mean().data,2)
        mean_sMF_sLC = diff_sMF_sLC.groupby(diff_sMF_sLC.time.dt.hour).mean()
        std_sMF_sLC = diff_sMF_sLC.groupby(diff_sMF_sLC.time.dt.hour).std()

        diff_sMF_uLCu = series_sMF_uLCu - series_up
        mae_diff_sMF_uLCu = np.round(diff_sMF_uLCu.mean().data,2)
        mean_sMF_uLCu = diff_sMF_uLCu.groupby(diff_sMF_uLCu.time.dt.hour).mean()
        std_sMF_uLCu = diff_sMF_uLCu.groupby(diff_sMF_uLCu.time.dt.hour).std()

        diff_uMF_sLC = series_uMF_sLC - series_up
        mae_diff_uMF_sLC = np.round(diff_uMF_sLC.mean().data,2)
        mean_uMF_sLC = diff_uMF_sLC.groupby(diff_uMF_sLC.time.dt.hour).mean()
        std_uMF_sLC = diff_uMF_sLC.groupby(diff_uMF_sLC.time.dt.hour).std()

        diff_uMF_uLCu = series_uMF_uLCu - series_up
        mae_diff_uMF_uLCu = np.round(diff_uMF_uLCu.mean().data,2)
        mean_uMF_uLCu = diff_uMF_uLCu.groupby(diff_uMF_uLCu.time.dt.hour).mean()
        std_uMF_uLCu = diff_uMF_uLCu.groupby(diff_uMF_uLCu.time.dt.hour).std()

        # plt.errorbar(mean_sMF_sLC.hour, mean_sMF_sLC, yerr= std_sMF_sLC)
        # plt.errorbar(mean_sMF_uLCu.hour, mean_sMF_uLCu, yerr= std_sMF_uLCu)
        # plt.errorbar(mean_uMF_sLC.hour, mean_uMF_sLC, yerr= std_uMF_sLC)
        # plt.errorbar(mean_uMF_uLCu.hour, mean_uMF_uLCu, yerr= std_uMF_uLCu)

        # Timeseries
        ax[v_i, 0].plot(diff_sMF_sLC, label='sMF_sLC', lw=4)
        ax[v_i, 0].plot(diff_sMF_uLCu, label='sMF_uLCu', lw=3)
        ax[v_i, 0].plot(diff_uMF_sLC, label='uMF_sLC', lw=2)
        ax[v_i, 0].plot(diff_uMF_uLCu, label='uMF_uLCu', lw=1)
        ax[v_i, 0].set_ylabel(var)
        ax[v_i, 0].legend()
        ax[v_i, 0].set_title(f"{var}: Model - Obs | "
                             f"MAE for sMF_sLC = {mae_diff_sMF_sLC} | "
                             f"sMF_uLCu = {mae_diff_sMF_uLCu} | "
                             f"uMF_sLC = {mae_diff_uMF_sLC} | "
                             f"uMF_uLCu = {mae_diff_uMF_uLCu}")

        # Diurnal Cycle
        ax[v_i, 1].plot(mean_sMF_sLC.hour, mean_sMF_sLC, label="sMF_sLC")
        ax[v_i, 1].fill_between(mean_sMF_sLC.hour, mean_sMF_sLC-std_sMF_sLC, mean_sMF_sLC+std_sMF_sLC, alpha=0.1)

        ax[v_i, 1].plot(mean_sMF_uLCu.hour, mean_sMF_uLCu, label="sMF_uLCu")
        ax[v_i, 1].fill_between(mean_sMF_uLCu.hour, mean_sMF_uLCu-std_sMF_uLCu, mean_sMF_uLCu+std_sMF_uLCu, alpha=0.1)

        ax[v_i, 1].plot(mean_uMF_sLC.hour, mean_uMF_sLC, label="uMF_sLC")
        ax[v_i, 1].fill_between(mean_uMF_sLC.hour, mean_uMF_sLC-std_uMF_sLC, mean_uMF_sLC+std_uMF_sLC, alpha=0.1)

        ax[v_i, 1].plot(mean_uMF_uLCu.hour, mean_uMF_uLCu, label="uMF_uLCu")
        ax[v_i, 1].fill_between(mean_uMF_uLCu.hour, mean_uMF_uLCu-std_uMF_uLCu, mean_uMF_uLCu+std_uMF_uLCu, alpha=0.1)

    plt.tight_layout()
    fig_name = os.path.join(
        fig_dir,
        f"{city}_check_output_fluxes_{gh_pr}.png"
    )
    plt.savefig(fig_name)
    plt.close('all')
