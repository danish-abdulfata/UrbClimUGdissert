import pandas as pd
import os
import numpy as np
os.environ['USE_PYGEOS'] = '0'
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import matplotlib as mpl
fontsize = 12
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams.update({'font.size': fontsize})
mpl.rcParams['legend.numpoints'] = 1

# output directories
fig_dir = '/home/demuzmp4/Dropbox/Apps/Overleaf/Demuzere_etal_supy-lcz (1)/figs'
o_dir = '/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/input/grid'
fn_rdp = f'{o_dir}/rdp_fractions_norm.nc'
ds = xr.open_dataset(fn_rdp)


def hex_to_RGB(hex_str):
    """ #FFFFFF -> [255,255,255]"""
    #Pass 16 to the integer function for change of base
    return [int(hex_str[i:i+2], 16) for i in range(1,6,2)]

def get_color_gradient(c1, c2, n):
    """
    Given two hex colors, returns a color gradient
    with n colors.
    """
    assert n > 1
    c1_rgb = np.array(hex_to_RGB(c1))/255
    c2_rgb = np.array(hex_to_RGB(c2))/255
    mix_pcts = [x/(n-1) for x in range(n)]
    rgb_colors = [((1-mix)*c1_rgb + (mix*c2_rgb)) for mix in mix_pcts]
    return ["#" + "".join([format(int(round(val*255)), "02x") for val in item]) for item in rgb_colors]

n_bin = 10
coldict = {
    'ROAD_N': ("#ffffff", "#757575", 'Road fraction [-]'),
    'BLD_N': ("#ffffff", "#881F1F", 'Building fraction [-]'),
    'VEGH_N': ("#ffffff", "#00390F", 'High vegetation fraction [-]'),
    'VEGB_N': ("#ffffff", "#009025", 'Low vegetation fraction [-]'),
    'NVEG_N': ("#ffffff", "#EADF9A", 'Bare soil fraction [-]'),
    'WATER_N': ("#ffffff", "#0090D3", 'Water fraction [-]'),
}

fig, axes = plt.subplots(2,3, sharey=True, sharex=True, figsize=(20,10))
axs = axes.flatten()

for v_i, var in enumerate(coldict.keys()):

    colors = get_color_gradient(coldict[var][0], coldict[var][1], n=n_bin)
    cmap = LinearSegmentedColormap.from_list(var, colors, N=n_bin)

    # Plot
    ds[var].plot(cmap=cmap, vmin=0, vmax=1, extend='neither',
                 ax=axs[v_i],
                 cbar_kwargs={'label': coldict[var][2]}
                 )
    axs[v_i].set_ylabel('')
    axs[v_i].set_xlabel('')

    if v_i in [0,3]:
        axs[v_i].set_ylabel('Latitude [°N]')

    if v_i >= 3:
        axs[v_i].set_xlabel('Longitude [°E]')

plt.tight_layout()

figfile = os.path.join(
    fig_dir,
    'rdp_fractions.png'
)
plt.savefig(figfile, dpi=300)
plt.close('all')