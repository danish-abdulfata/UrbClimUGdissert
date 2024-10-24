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
plt.rcParams['font.size'] = 18

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
city = 'NL-Amsterdam'

site_info = get_city_from_site_list(city)

# Memory issues, save forcing firts
# timestep = site_info['timestep_interval_seconds']
# if timestep == 1800:
#     steps = 6
# else:
#     steps=12
#
# sim = '1_1b'
# #sim = '3_1b'
# fn = f'{fn_dir}/{city}/output/buffer/df_final_forcing_{sim}.h5'
# df = pd.read_hdf(fn, parse_dates=True, key="df_forcing")
# #ds_1_1b_r = resample_forcing(ds_1_1b, timestep)
# df = df.iloc[::steps,:]
#
# fn_csv = f'/home/demuzmp4/GoogleDrive/work-official/conferences/EGU2023/presentation/df_{sim}_kdown.csv'
# df['kdown'].to_csv(fn_csv)

# Now read back in, and plot the results.
sim = '1_1b'
fn_obs = f'/home/demuzmp4/GoogleDrive/work-official/conferences/EGU2023/presentation/df_{sim}_kdown.csv'
df_obs = pd.read_csv(fn_obs, parse_dates=True, index_col=[0])
sim = '3_1b'
fn_era = f'/home/demuzmp4/GoogleDrive/work-official/conferences/EGU2023/presentation/df_{sim}_kdown.csv'
df_era = pd.read_csv(fn_era, parse_dates=True, index_col=[0])

fig, ax = plt.subplots(1,1, figsize=(25,7))
ax.set_ylabel(r'K$\downarrow$ [W/m-2]')
ax.set_xlabel(r'Date')
df_obs[site_info['time_coverage_start']:site_info['time_analysis_start']].\
    plot(ax=ax, color='#f44505', label='spin-up',legend=None)
df_obs[site_info['time_analysis_start']:site_info['time_coverage_end']].\
    plot(ax=ax, color='0.2', label='analysis - obs',legend=None)
plt.tight_layout()
fig_obs = "/home/demuzmp4/GoogleDrive/work-official/conferences/EGU2023/presentation/Figure_obs.png"
plt.savefig(fig_obs, dpi=300)
df_era[site_info['time_analysis_start']:site_info['time_coverage_end']].\
    plot(ax=ax, color='#2877b4', label='analysis - era5land',legend=None)
fig_obs = "/home/demuzmp4/GoogleDrive/work-official/conferences/EGU2023/presentation/Figure_era.png"
plt.savefig(fig_obs, dpi=300)
