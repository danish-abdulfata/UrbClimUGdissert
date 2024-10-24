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

# Read in the surface fraction data
sfr_class = {
    'Paved': '#3E3E3E',
    'Bldgs': '#BB0003',
    'EveTr': '#507A50',
    'DecTr': '#03D400',
    'Grass': '#36FFB0',
    'BSoil': '#DE9D54',
    'Water': '#5FB2E8',
}


# Plot the surface cover fractions as stacked bars.
fig, axes = plt.subplots(3,7, figsize=(15,10),
                       sharey=True, sharex=True)
ax = axes.flatten()

for s_i, site in enumerate(sites):

    sfr_arr = np.zeros((len(sim_codes), len(sfr_class)))
    popden_arr = np.zeros((len(sim_codes), 3))

    for i, sim_code in enumerate(sim_codes):
        fn_state = os.path.join(
            fn_dir,
            'data',
            site,
            f"output/df_state_{sim_code}.pkl"
        )
        df_state = pd.read_pickle(fn_state)
        sfr_arr[i, :] = df_state['sfr_surf'].values
        popden_arr[i, :2] = df_state['popdensdaytime'].values
        popden_arr[i, 2] = df_state['popdensnighttime'].values

    bottom = np.zeros(len(sim_codes))
    for i in range(len(sfr_class)):
        ax[s_i].bar(range(len(sim_codes)), sfr_arr[:,i],
                bottom=sfr_arr[:,:i].sum(axis=1),
                label=list(sfr_class.keys())[i],
                color=list(sfr_class.values())[i]
               )
        # bottom += sfr_arr[:,i]
        # print(bottom)

    # Add the population density numbers above the plot
    for i in range(3):
        for y_i in range(len(sim_codes)):
            ax[s_i].text(y_i, 1.20-(i*0.05), np.round(popden_arr[y_i,i],1),
                horizontalalignment='center', fontsize=8)

    # ax[s_i].text(-0.8, 1.15, 'Popden Day - Week', horizontalalignment='right', fontsize=8)
    # ax[s_i].text(-0.8, 1.10, 'Popden Day - Weekend', horizontalalignment='right', fontsize=8)
    # ax[s_i].text(-0.8, 1.05, 'Popden Night', horizontalalignment='right', fontsize=8)

    if s_i in [0, 7, 14]:
        ax[s_i].set_ylabel("Surface area fraction [-]")
    ax[s_i].set_title(site, fontsize=9)

    ax[s_i].set_xticks(range(len(sim_codes)))
    ax[s_i].set_xticklabels(sim_codes, fontsize=11)

plt.tight_layout()

# Add legend below subplots
leg_elements = [
    Patch(facecolor=sfr_class[key], edgecolor='0.5',
          label=f"{key}")  # , markerfacecolor=None
    for key in sfr_class.keys()
]
surf_legend = fig.legend(handles=leg_elements,
                        bbox_to_anchor=(0.5, 0.05), ncol=7,
                        loc='center', fontsize=11,
                        numpoints=1, scatterpoints=1
                        )

plt.subplots_adjust(bottom=0.1)
plt.gca().add_artist(surf_legend)

# Save
FIG_FILE = os.path.join(
    figdir,
    "df_state_sfr_surf_allsims.pdf"
)
plt.savefig(FIG_FILE, dpi=300)
plt.close(fig)

print(f"Figure available at: {FIG_FILE}")