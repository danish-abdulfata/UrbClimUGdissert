import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import dataframe_image as dfi
from pathlib import Path

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams.update({'font.size': 10})
mpl.rcParams['legend.numpoints'] = 1
from matplotlib.patches import Patch

import warnings
warnings.filterwarnings("ignore")

#fn_dir = "/data/"
fn_dir = "/home/demuzmp4/Nextcloud/scripts/supy-lcz-global"

# Urban description experiments
sim_codes = ['2_1a', '2_1b', '2_2a', '2_2b']

# sites
site_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
sites = list(site_list['sitename'].values);

# Create folder to store tmp figures
figdir = Path("/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/figs")
figdir.mkdir(parents=True, exist_ok=True)

## Plot relevant state variables in a table?
dict_rule_columns = {
    ('sfr_surf', '(0,)'): 'Paved (-)',
    ('sfr_surf', '(1,)'): 'Buildings (-)',
    ('sfr_surf', '(4,)'): 'Grass (-)',
    ('sfr_surf', '(3,)'): 'Deciduous trees (-)',
    ('sfr_surf', '(2,)'): 'Evergreen trees (-)',
    ('sfr_surf', '(5,)'): 'Bare soil (-)',
    ('sfr_surf', '(6,)'): 'Water (-)',
    ('bldgh', '0'): 'Mean building height (m)',
    ('evetreeh', '0'): 'Mean vegetation height evergeen (m)',
    ('dectreeh', '0'): 'Mean vegetation height deciduous (m)',
    ('faibldg', '0'): 'Frontal area index buildings (-)',
    ('faievetree', '0'): 'Frontal area index vegetation evergeen (-)',
    ('faidectree', '0'): 'Frontal area index vegetation deciduous (-)',
    ('popdensdaytime', '(0,)'): 'Daytime population density (i.e. workers, tourists) [people ha-1] [Week]',
    ('popdensdaytime', '(1,)'): 'Daytime population density (i.e. workers, tourists) [people ha-1] [Weekend]',
    ('popdensnighttime', '0'): 'Night-time population density (i.e. residents) [people ha-1]',
    ('z0m_in', '0'): 'Roughness length for momentum (m)',
    ('zdm_in', '0'): 'Zero-plane displacement height (m)',
    ('alb', '(0,)'): 'Effective surface albedo (middle of the day value) for summertime.', # All other albedos are the same
}

# Loop over all sites
for site in sites:
    df_table = pd.DataFrame(
        index = [i for i in dict_rule_columns.values()],
        columns = sim_codes
    )

    for sim_code in sim_codes:

        fn_state = os.path.join(
            fn_dir,
            'data',
            site,
            f"output/df_state_{sim_code}.pkl"
        )
        df_state = pd.read_pickle(fn_state)
        df_table.loc[:,sim_code] = df_state.loc[:, dict_rule_columns.keys()].values.flatten()

    # TABLE_FILE = os.path.join(
    #     figdir,
    #     f"{site}_df_state_table.csv"
    # )
    # df_table.to_csv(TABLE_FILE)

    # Save as image for quick check
    TABLE_FILE_IMG = os.path.join(
        figdir,
        f"{site}_df_state_table.png"
    )
    dfi.export(df_table, TABLE_FILE_IMG)