"""

NOTE: This code has been implemented in the runner itself,
to be done automatically using argument --use-rdp

"""

from __future__ import annotations
import os
os.environ['USE_PYGEOS'] = '0'
import geopandas as gpd
import xarray as xr
import pandas as pd
from pathlib import Path

# Paths
fn_base = Path('data/FR-Paris')
fn_state = fn_base / 'output' / 'grid' / 'df_state_uMF_uLCu.pkl'
fn_grid = fn_base / 'input' / 'grid' / 'roi_grid.shp'
fn_rdp = fn_base / 'input' / 'grid' / 'rdp_fractions_norm.nc'

# Read and prepare files
df_state = pd.read_pickle(fn_state)
grid = gpd.read_file(fn_grid)
rdp = xr.open_dataset(fn_rdp)
rdp = rdp.rio.write_crs(grid.crs)
rdp = rdp.rename({'Lat':'y', 'Lon': 'x'})

# Info on clip: https://corteva.github.io/rioxarray/html/examples/clip_geom.html
# Create dataframe to store fractions in, per grid id
sfr_rdp = [
        'ROAD_N',
        'BLD_N',
        'VEGB_N',
        'VEGH_N',
        'NVEG_N',
        'WATER_N'
    ]
df_fractions = pd.DataFrame(
    index=df_state.index,
    columns=sfr_rdp
)

for i in grid.index:
    print(i)
    for sfr in sfr_rdp:
        df_fractions.loc[i, sfr] = \
            float(rdp.rio.clip(gpd.GeoSeries(grid.geometry[i])).mean()[sfr])

# Check if fractions round to 1
fr_sum = df_fractions[df_fractions.sum(axis=1).astype(float).round(2) == 1.0]
if fr_sum.shape[0] != grid.shape[0]:
    print('ERROR: not all grid cells have fractions that sum to 1')

# Repurpose the df_fractions: split trees evenly to evergeen and deciduous
df_fractions['VEGH_N_EVE'] = df_fractions['VEGH_N'] / 2
df_fractions['VEGH_N_DEC'] = df_fractions['VEGH_N'] / 2

# Put in state a new state used for the RDP experiment
df_state_rdp = df_state.copy()
df_state_rdp.loc[:, 'sfr_surf']

dict_rule_columns = {
    ('sfr_surf', '(0,)'): 'ROAD_N',
    ('sfr_surf', '(1,)'): 'BLD_N',
    ('sfr_surf', '(2,)'): 'VEGH_N_EVE',
    ('sfr_surf', '(3,)'): 'VEGH_N_DEC',
    ('sfr_surf', '(4,)'): 'VEGB_N',
    ('sfr_surf', '(5,)'): 'NVEG_N',
    ('sfr_surf', '(6,)'): 'WATER_N',
}
df_state_rdp.loc[:, dict_rule_columns.keys()] = \
        df_fractions.loc[:, dict_rule_columns.values()].values

# Save new state to pickle
state_file = str(fn_state).replace('.pkl', '_rdp.pkl')
df_state_rdp.to_pickle(state_file)
df_state_rdp.loc[:, dict_rule_columns.keys()]
