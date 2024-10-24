import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
import supy

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams.update({'font.size': 10})
mpl.rcParams['legend.numpoints'] = 1
from matplotlib.patches import Patch

import warnings
warnings.filterwarnings("ignore")

# Set STATE to explore
state_var = "emissionsmethod"
state_var = 'popdensdaytime'
#state_var = 'popdensnighttime'

#fn_dir = "/data/"
fn_dir = "/home/demuzmp4/Nextcloud/scripts/supy-lcz-global"

# Urban description experiments
sim_codes = ['1_1b'] #, '1_2b']

# sites
site_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
sites = list(site_list['sitename'].values);
sites = ["FI-Torni"]
sites = ["AU-Preston"]

# Loop over all sites
for site in sites:

    #site = "AU-Preston"

    for sim_code in sim_codes:

        #sim_code = "1_2b"

        fn_state = os.path.join(
            fn_dir,
            'data',
            site,
            "output",
            "buffer",
            f"df_state_{sim_code}.pkl"
        )
        df_state = pd.read_pickle(fn_state)
        print_state = df_state.loc[:, state_var]

        # How much in init sample?
        df_state_init, _ = supy.load_SampleData()
        print_state_init = df_state_init.loc[:, state_var]


        print(f"***** {site} | {sim_code}: {print_state} *****")
        print(f"***** In INIT: {print_state_init} *****")