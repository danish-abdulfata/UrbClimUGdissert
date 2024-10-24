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



# sites
site_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
sites = list(site_list['sitename'].values);
site = 'NL-Amsterdam'

# Urban description experiments
sim_code = '3_2b'

# Grid IDs
ids = [85-1, 153-1]

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

# Read the state
fn_state = os.path.join(
    fn_dir,
    'data',
    site,
    f"output/grid/df_state_{sim_code}.pkl"
)
df_state = pd.read_pickle(fn_state)

sfr_arr = np.zeros((len(ids), len(sfr_class)))
popden_arr = np.zeros((len(ids), 3))

for ix, i in enumerate(ids):
    sfr_arr[ix, :] = df_state.loc[i, 'sfr_surf'].values
    popden_arr[ix, :2] = df_state.loc[i, 'popdensdaytime'].values
    popden_arr[ix, 2] = df_state.loc[i, 'popdensnighttime'].values

# Plot the surface cover fractions as stacked bars.
fig, ax = plt.subplots(1,1, figsize=(6,10),
                       sharey=True, sharex=True)

bottom = np.zeros(len(ids))
for i in range(len(sfr_class)):
    ax.bar(range(len(ids)), sfr_arr[:,i],
            bottom=sfr_arr[:,:i].sum(axis=1),
            label=list(sfr_class.keys())[i],
            color=list(sfr_class.values())[i]
           )

ax.set_ylabel("Surface area fraction [-]")

ax.set_xticks(range(len(ids)))
ax.set_xticklabels(ids, fontsize=fontsize)

plt.tight_layout()


# Save
FIG_FILE = os.path.join(
    figdir,
    "df_state_sfr_surf_grid.png"
)
plt.savefig(FIG_FILE, dpi=300)
plt.close(fig)

print(f"Figure available at: {FIG_FILE}")

# # Check building height from state?
# fn_state = "/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/data/NL-Amsterdam/output/buffer/df_state_final_3_2b.pkl"
# df = pd.read_pickle(fn_state)