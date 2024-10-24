import pandas as pd
import os
import numpy as np
os.environ['USE_PYGEOS'] = '0'
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path
import matplotlib as mpl
from geocube.api.core import make_geocube
fontsize = 12
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams.update({'font.size': fontsize})
mpl.rcParams['legend.numpoints'] = 1

# output directories
fig_dir = Path('/home/demuzmp4/Dropbox/Apps/Overleaf/Demuzere_etal_supy-lcz (1)/figs')
i_dir = Path('/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/input/grid')
o_dir = Path('/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/output/grid')

# Files
fn_state_lcz = o_dir / "df_state_uMF_uLCu.pkl"
fn_state_rdp = o_dir / "df_state_uMF_uLCu_rdp.pkl"
fn_grid = i_dir / "roi_grid.shp"


# Read the files
gdf_grid = gpd.read_file(fn_grid)
df_state_lcz = pd.read_pickle(fn_state_lcz)
df_state_rdp = pd.read_pickle(fn_state_rdp)

# Are the state actually completely different??
np.sum(df_state_lcz.loc[:, 'sfr_surf'] != df_state_rdp.loc[:, 'sfr_surf'])


# 1) Plot fractions as histograms - collapsign spatial component
bins = np.arange(0, 0.5, 0.025)
coldict = {
    ('sfr_surf', '(0,)'): ("#ffffff", "#d0d0d0", 'Roads'),
    ('sfr_surf', '(1,)'): ("#ffffff", "#AA4A44", 'Buildings'),
    ('sfr_surf', '(2,)'): ("#ffffff", "#355E3B", 'Evergreen trees'),
    ('sfr_surf', '(3,)'): ("#ffffff", "#228B22", 'Deciduous trees'),
    ('sfr_surf', '(4,)'): ("#ffffff", "#cfe4c2", 'Grass'),
    #('sfr_surf', '(5,)'): ("#ffffff", "#0090D3", 'Bare soil fraction [-]'),
    ('sfr_surf', '(6,)'): ("#ffffff", "#a9c8e3", 'Water'),
}

fig, axes = plt.subplots(2,3, sharey=True, sharex=True, figsize=(20,10))
axs = axes.flatten()

for v_i, var in enumerate(coldict.keys()):

    # Do I want to filter out certain values?
    lcz_values = df_state_lcz.loc[:, var][df_state_lcz.loc[:, var] >= 0]
    rdp_values = df_state_rdp.loc[:, var][df_state_rdp.loc[:, var] >= 0]

    lcz_values.hist(
        bins=bins, ax=axs[v_i], zorder=10,
        color=coldict[var][1],
        label='LCZ-based',
    )

    rdp_values.hist(
        bins=bins, ax=axs[v_i], zorder=10,
        edgecolor='0.2', lw=1,
        #facecolor=colors[1], alpha=0.3,
        facecolor="None",
        hatch='////', fill=True,
        label='RDP-based',
    )

    axs[v_i].set_title(coldict[var][2])
    if v_i in [3,4,5]:
        axs[v_i].set_xlabel('Fraction [-]')
    if v_i in [0,3]:
        axs[v_i].set_ylabel('Frequency [-]')

    if v_i == 0:
        axs[v_i].legend(loc="upper left")

plt.tight_layout()

figfile = os.path.join(
    fig_dir,
    'lcz_rdp_fractions_histogram.png'
)
plt.savefig(figfile, dpi=300)
plt.close('all')

# 2) Make spatial maps and their differences, on simulation resolution
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
    '(0,)': ("#ffffff", "#424040", 'Roads'),
    '(1,)': ("#ffffff", "#AA4A44", 'Buildings'),
    '(2,)': ("#ffffff", "#355E3B", 'Evergreen trees'),
    '(3,)': ("#ffffff", "#228B22", 'Deciduous trees'),
    '(4,)': ("#ffffff", "#cfe4c2", 'Grass'),
    #'(5,)': ("#ffffff", "#0090D3", 'Bare soil fraction [-]'),
    '(6,)': ("#ffffff", "#a9c8e3", 'Water'),
}

# Clean grid file
gdf_grid.index = gdf_grid['id']
#gdf_grid.drop(['id', 'some_col'], axis=1, inplace=True)
gdf_grid.index.name = "grid"

# Add values to geometries.
gdf_frc_lcz = gdf_grid.join(df_state_lcz.loc[:, 'sfr_surf'])
gdf_frc_rdp = gdf_grid.join(df_state_rdp.loc[:, 'sfr_surf'])

# Convert to raster using geocube
rdp_norm = xr.open_dataset("/media/demuzmp4/MAFFIE2TB/RUB/supy-lcz-global-data/FR-Paris/input/grid/rdp_fractions_norm.nc")
rdp_norm = rdp_norm.rename({'Lat':'y', 'Lon': 'x'})
rdp_norm = rdp_norm.rio.write_crs(gdf_grid.crs)

frc_lcz_raster = make_geocube(vector_data=gdf_frc_lcz, like=rdp_norm)
frc_rdp_raster = make_geocube(vector_data=gdf_frc_rdp, like=rdp_norm)

# Now plot as maps
fig, axes = plt.subplots(3,6, sharey=True, sharex=True, figsize=(17,10))

for v_i, var in enumerate(coldict.keys()):

    ## Fraction type specific colors
    #colors = get_color_gradient(coldict[var][0], coldict[var][1], n=n_bin)

    # Grey-scale for all fraction types
    colors = get_color_gradient(coldict['(0,)'][0], coldict['(0,)'][1], n=n_bin)

    cmap = LinearSegmentedColormap.from_list(var, colors, N=n_bin)

    # gdf_frc_lcz.plot(
    #     column=var,
    #     ax=axes[0, v_i],
    #     cmap=cmap, vmin=0, vmax=0.5,
    # )
    # gdf_frc_rdp.plot(
    #     column=var,
    #     ax=axes[1, v_i],
    #     cmap=cmap, vmin=0, vmax=0.5,
    # )

    im1 = frc_lcz_raster[var].plot(
        ax=axes[0, v_i],
        cmap=cmap, vmin=0, vmax=0.7,
        add_colorbar=False,
    )
    frc_rdp_raster[var].plot(
        ax=axes[1, v_i],
        cmap=cmap, vmin=0, vmax=0.7,
        add_colorbar=False,
    )
    im2 = (frc_lcz_raster[var] - frc_rdp_raster[var]).plot(
        ax=axes[2, v_i],
        cmap=plt.get_cmap('PuOr'), vmin=-0.5, vmax=0.5,
        add_colorbar=False,
    )

    axes[0,v_i].set_title(coldict[var][2])
    axes[1, v_i].set_title('')
    axes[2, v_i].set_title('')

    axes[0, v_i].set_ylabel('')
    axes[1, v_i].set_ylabel('')
    axes[2, v_i].set_ylabel('')

    axes[0, v_i].set_xlabel('')
    axes[1, v_i].set_xlabel('')
    axes[2, v_i].set_xlabel('')

    #axes[y_i, v_i].set_xlabel('')

    if v_i == 0 :
        axes[0, v_i].set_ylabel('Latitude [°N]')
        axes[1, v_i].set_ylabel('Latitude [°N]')
        axes[2, v_i].set_ylabel('Latitude [°N]')

    axes[2, v_i].set_xlabel('Longitude [°E]')

plt.tight_layout()

# Add two legends
plt.subplots_adjust(right=0.94)
cax1 = plt.axes([0.945, 0.5, 0.015, 0.3])
cax2 = plt.axes([0.945, 0.13, 0.015, 0.15])
fig.colorbar(im1, ax=axes[:1, :], cax=cax1)
fig.colorbar(im2, ax=axes[2, :], cax=cax2)

figfile = os.path.join(
    fig_dir,
    'lcz_rdp_diff_fractions_2Dmap.png'
)
plt.savefig(figfile, dpi=300)
plt.close('all')






#
# n_bin = 10
# coldict = {
#     'ROAD_N': ("#ffffff", "#757575", 'Road fraction [-]'),
#     'BLD_N': ("#ffffff", "#881F1F", 'Building fraction [-]'),
#     'VEGH_N': ("#ffffff", "#00390F", 'High vegetation fraction [-]'),
#     'VEGB_N': ("#ffffff", "#009025", 'Low vegetation fraction [-]'),
#     'NVEG_N': ("#ffffff", "#EADF9A", 'Bare soil fraction [-]'),
#     'WATER_N': ("#ffffff", "#0090D3", 'Water fraction [-]'),
# }
#
# fig, axes = plt.subplots(2,3, sharey=True, sharex=True, figsize=(20,10))
# axs = axes.flatten()
#
# for v_i, var in enumerate(coldict.keys()):
#
#     colors = get_color_gradient(coldict[var][0], coldict[var][1], n=n_bin)
#     cmap = LinearSegmentedColormap.from_list(var, colors, N=n_bin)
#
#     # Plot
#     ds[var].plot(cmap=cmap, vmin=0, vmax=1, extend='neither',
#                  ax=axs[v_i],
#                  cbar_kwargs={'label': coldict[var][2]}
#                  )
#     axs[v_i].set_ylabel('')
#     axs[v_i].set_xlabel('')
#
#     if v_i in [0,3]:
#         axs[v_i].set_ylabel('Latitude [°N]')
#
#     if v_i >= 3:
#         axs[v_i].set_xlabel('Longitude [°E]')
#
# plt.tight_layout()
#
# figfile = os.path.join(
#     fig_dir,
#     'rdp_fractions.png'
# )
# plt.savefig(figfile, dpi=300)
# plt.close('all')