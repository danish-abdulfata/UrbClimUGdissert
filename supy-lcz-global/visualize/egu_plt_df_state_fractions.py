import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams.update({'font.size': 18})
mpl.rcParams['legend.numpoints'] = 1
from matplotlib.patches import Patch
fontsize = 18

import warnings
warnings.filterwarnings("ignore")

#fn_dir = "/data/"
fn_dir = "/home/demuzmp4/Nextcloud/scripts/supy-lcz-global"

# Urban description experiments
sim_codes = ['1_1b', '1_2b']

# sites
site_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
sites = list(site_list['sitename'].values);
sites = ['NL-Amsterdam']

# Create folder to store tmp figures
figdir = Path("/home/demuzmp4/GoogleDrive/work-official/conferences/EGU2023/presentation")
figdir.mkdir(parents=True, exist_ok=True)

# Read in the surface fraction data
sfr_class = {
    'Paved': '#c0bebf',
    'Bldgs': '#cac5c9',
    'EveTr': '#bcc8b4',
    'DecTr': '#c7d8ba',
    'Grass': '#cfe4c2',
    'BSoil': '#eed9ae',
    'Water': '#a9c8e3',
}


# Plot the surface cover fractions as stacked bars.
fig, ax = plt.subplots(1,1, figsize=(6,10),
                       sharey=True, sharex=True)

for s_i, site in enumerate(sites):

    sfr_arr = np.zeros((len(sim_codes), len(sfr_class)))
    popden_arr = np.zeros((len(sim_codes), 3))

    for i, sim_code in enumerate(sim_codes):
        fn_state = os.path.join(
            fn_dir,
            'data',
            site,
            f"output/buffer/df_state_{sim_code}.pkl"
        )
        df_state = pd.read_pickle(fn_state)
        sfr_arr[i, :] = df_state['sfr_surf'].values
        popden_arr[i, :2] = df_state['popdensdaytime'].values
        popden_arr[i, 2] = df_state['popdensnighttime'].values

    bottom = np.zeros(len(sim_codes))
    for i in range(len(sfr_class)):
        ax.bar(range(len(sim_codes)), sfr_arr[:,i],
                bottom=sfr_arr[:,:i].sum(axis=1),
                label=list(sfr_class.keys())[i],
                color=list(sfr_class.values())[i]
               )
        # bottom += sfr_arr[:,i]
        # print(bottom)

    # Add the population density numbers above the plot
    for i in range(3):
        for y_i in range(len(sim_codes)):
            ax.text(y_i, 1.20-(i*0.05), np.round(popden_arr[y_i,i],1),
                horizontalalignment='center', fontsize=fontsize)

    # ax[s_i].text(-0.8, 1.15, 'Popden Day - Week', horizontalalignment='right', fontsize=8)
    # ax[s_i].text(-0.8, 1.10, 'Popden Day - Weekend', horizontalalignment='right', fontsize=8)
    # ax[s_i].text(-0.8, 1.05, 'Popden Night', horizontalalignment='right', fontsize=8)

    if s_i in [0, 7, 14]:
        ax.set_ylabel("Surface area fraction [-]")
    ax.set_title(site, fontsize=fontsize)

    ax.set_xticks(range(len(sim_codes)))
    ax.set_xticklabels(sim_codes, fontsize=fontsize)

plt.tight_layout()

# Add legend below subplots
leg_elements = [
    Patch(facecolor=sfr_class[key], edgecolor='0.5',
          label=f"{key}")  # , markerfacecolor=None
    for key in sfr_class.keys()
]
surf_legend = fig.legend(handles=leg_elements,
                        bbox_to_anchor=(0.5, 0.03), ncol=4,
                        loc='center', fontsize=14,
                        numpoints=1, scatterpoints=1
                        )

plt.subplots_adjust(bottom=0.1)
plt.gca().add_artist(surf_legend)

# Save
FIG_FILE = os.path.join(
    figdir,
    "df_state_sfr_surf_allsims.png"
)
plt.savefig(FIG_FILE, dpi=300)
plt.close(fig)

print(f"Figure available at: {FIG_FILE}")

# Check building height from state?
fn_state = "/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/data/NL-Amsterdam/output/buffer/df_state_final_3_2b.pkl"
df = pd.read_pickle(fn_state)