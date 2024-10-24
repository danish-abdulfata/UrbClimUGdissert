import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams.update({'font.size': 10})
mpl.rcParams['legend.numpoints'] = 1
from matplotlib.patches import Patch

import warnings
warnings.filterwarnings("ignore")

# Set STATE to explore
state_var = "emissionsmethod"

#fn_dir = "/data/"
fn_dir = "/home/demuzmp4/Nextcloud/scripts/supy-lcz-global"

# SITE
site = "AU-Preston"
site = "FI-Torni"

# EXPIREMENT
#sim_code = "1_2b"
#sim_code = "1_1b"
sim_code = "3_1b"

# STATE VARIABLE
state_var = 'emissionsmethod'
state_var = 'tstep'
state_var = 'tstep_prev'
state_var = 'daily_state'

fn_state = os.path.join(
    fn_dir,
    'data',
    site,
    f"output/df_state_{sim_code}.pkl"
)
df_state = pd.read_pickle(fn_state)
print_state = df_state.loc[:, state_var]
print(f"***** {site} | {sim_code}: {print_state} *****")

fn_state_final = os.path.join(
    fn_dir,
    'data',
    site,
    f"output/df_state_final_{sim_code}.pkl"
)
df_state_final = pd.read_pickle(fn_state_final)
print_state_final = df_state_final.loc[:, state_var]


# Check output
output_var = "AlbSnow"
output_var = "DaysSR"
output_var = "DensSnow_Paved"
output_var = "GDD_EveTr"
output_var = "HDD2_c"

fn_output = os.path.join(
    fn_dir,
    'data',
    site,
    f"output/df_output_{sim_code}.h5"
)
df_output = pd.read_hdf(fn_output)
print_output = df_output.loc[:, output_var]
print(f"***** {site} | {sim_code}: {print_output} *****")

# Read the forcing
fn_forcing = os.path.join(
    fn_dir,
    'data',
    site,
    f"output/df_final_forcing_{sim_code}.h5"
)
df_forcing = pd.read_hdf(fn_forcing)

# Select only one year
df_forcing_sel = df_forcing.loc['2013-01-01':'2013-12-31']

