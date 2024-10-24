import pandas as pd
import os
os.environ['USE_PYGEOS'] = '0'
import rioxarray as rxr
import xarray as xr

# output directory
o_dir = '/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/input/grid'

# LCZ file, used to crop large RDP domain
fn_lcz = "/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/input/grid/download.LCZ_Filter.tif"

# Helper functions
def crop_rdp(df, fn_lcz):

    # Domain is way to big, reduce to relevant coordinates
    # Read from grid shapefile
    # fn_grid = "/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/input/grid/roi_grid.shp"
    # gdf = gpd.read_file(fn_grid)

    lcz = rxr.open_rasterio(fn_lcz)
    xmin = float(lcz.x.min())
    xmax = float(lcz.x.max())
    ymin = float(lcz.y.min())
    ymax = float(lcz.y.max())

    print(xmin, xmax, ymin, ymax)

    # Slide dataframe to these bounds
    df_sel = df[
        (df.Lat > ymin) & (df.Lat < ymax) &
        (df.Lon > xmin) & (df.Lon < xmax)
    ]

    return df_sel

def get_xr_dataarray(df, var_name):

    # Now put in xarray dataset
    df_pv = df.pivot(index="Lat", columns="Lon")

    # drop first level of columns as it's not necessary
    df_pv = df_pv.droplevel(0, axis=1)

    # Convert to dataarray
    da = xr.DataArray(data=df_pv, name=var_name)

    # Fill nans with 0
    #da = da.fillna(0)

    return da

def combine_all(var_names, fn_lcz, o_dir, o_name):

    for var_name in var_names:

        # Define the RDP input file.
        #fn_rdp = f"/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/" \
        #     f"input/transfer_5185053_files_5895bb43/OSM_MNH_100m_{var_name}_LAT_LON.txt"

        fn_rdp = f"/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/" \
             f"transfer_5274585_files_b259f936/OSM_AROME_500m_SUPY_100m_{var_name}.txt"

        # Read the data
        df = pd.read_csv(fn_rdp, sep=' ', header=None)
        #df.columns = ['Lat', 'Lon', 'Var']
        df.columns = ['Lon', 'Lat', 'Var']

        # Crop the data
        df = crop_rdp(df, fn_lcz)

        # Get the xarray dataarray
        da_var = get_xr_dataarray(df, var_name)

        # Combine into one
        if var_name == "BLD" or var_name == "BLD_HEIGHT":
            da = da_var.copy()
        else:
            da = xr.merge([da, da_var])

    # Save as netcdf
    OFILE = os.path.join(
        o_dir,
        f"{o_name}.nc",
    )
    da.to_netcdf(OFILE)



# Read the file
# var_names = [
#     'BUILDING_FRACTION',
#     'ROAD_FRACTION',
#     'HIGH_VEGETATION_FRACTION',
#     'LOW_VEGETATION_FRACTION',
#     'NVEG_FRACTION',
#     'WATER',
#     'NATURE',
#     'SEA',
#     'TOWN',
# ]
var_names = [
    'BLD',
    #'BLD_HEIGHT',
    'ROAD',
    'VEGH', # High vegetation
    'VEGB', # Low vegetation
    'NVEG',
    'WATER',
    'NATURE',
    'SEA',
    'TOWN',
]

combine_all(var_names, fn_lcz, o_dir, 'rdp_fractions')

# var_names = [
#     'BUILDING_HEIGHT',
#     'WALL_O_HOR',
# ]
# combine_all(var_names, fn_lcz, o_dir, 'rdp_other')


# # Check the fractions
# da = xr.open_dataset("/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/input/grid/rdp_fractions.nc")
#
# da_sum = da['BUILDING_FRACTION'] + \
#          da['ROAD_FRACTION'] + \
#          da['HIGH_VEGETATION_FRACTION'] + \
#          da['LOW_VEGETATION_FRACTION'] + \
#          da['NVEG_FRACTION'] + \
#          da['WATER']
# da_sum.plot()
#
# da_sum = da['NATURE'] + \
#          da['SEA'] + \
#          da['WATER'] + \
#          da['TOWN']
# da_sum.plot()
#
# # ## Seperately
# var_name = 'BUILDING_FRACTION'
# fn_rdp = f"/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/" \
#          f"input/transfer_5185053_files_5895bb43/OSM_MNH_100m_{var_name}_LAT_LON.txt"
# df_BF = pd.read_csv(fn_rdp, sep=' ', header=None)
# df_BF.columns = ['Lat', 'Lon', 'Var']
# df_BF = crop_rdp(df_BF, fn_lcz)
# da_BF = get_xr_dataarray(df_BF, var_name)
#
# # ## Seperately
# # var_name = 'HIGH_VEGETATION_FRACTION'
# # fn_rdp = f"/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/" \
# #          f"input/transfer_5185053_files_5895bb43/OSM_MNH_100m_{var_name}_LAT_LON.txt"
# # df_HVF = pd.read_csv(fn_rdp, sep=' ', header=None)
# # df_HVF.columns = ['Lat', 'Lon', 'Var']
# # df_HVF = crop_rdp(df_HVF, fn_lcz)
# # da_HVF = get_xr_dataarray(df_HVF, var_name)
#
# # Check for NaNs:
#
# var_names = [
#     'BUILDING_FRACTION',
#     'ROAD_FRACTION',
#     'HIGH_VEGETATION_FRACTION',
#     'LOW_VEGETATION_FRACTION',
#     'NVEG_FRACTION',
#     'WATER',
#     'NATURE',
#     'SEA',
#     'TOWN',
#     'BUILDING_HEIGHT',
#     'WALL_O_HOR',
# ]
#
# for var_name in var_names:
#     fn_rdp = f"/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/" \
#              f"input/transfer_5185053_files_5895bb43/OSM_MNH_100m_{var_name}_LAT_LON.txt"
#     df_BF = pd.read_csv(fn_rdp, sep=' ', header=None)
#     df_BF.columns = ['Lat', 'Lon', 'Var']
#     print(f"{var_name}: {np.sum(np.isnan(df_BF['Var']))} NaNs")
#
# # # Counts of unique values
# var_name = 'BUILDING_FRACTION'
# fn_rdp = f"/home/demuzmp4/Nextcloud/data/supy-lcz-global-data/FR-Paris/" \
#          f"input/transfer_5185053_files_5895bb43/OSM_MNH_100m_{var_name}_LAT_LON.txt"
# df = pd.read_csv(fn_rdp, sep=' ', header=None)
# df.columns = ['Lat', 'Lon', 'Var']
# #print(df_BF['Lon'].value_counts())
#
# df_crop = crop_rdp(df, fn_lcz)
#
# # Area that has no values in grid
# xmin = 2.2445; xmax = 2.2447
# ymin = 48.852; ymax = 48.857
#
# df_nan = df_crop[
#     (df_crop.Lat > ymin) & (df_crop.Lat < ymax) &
#     (df_crop.Lon > xmin) & (df_crop.Lon < xmax)
#     ]
# print(df_nan)

