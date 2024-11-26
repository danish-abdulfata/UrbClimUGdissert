import argparse
import pandas as pd
import matplotlib.pyplot as plt
import rioxarray
import xarray as xr
from pathlib import Path
import geopandas as gpd
import numpy as np
from pyproj import CRS
from pyproj import Transformer


def convert_h5_to_netcdf(input_file, dx, lat, lon):
    """
    Convert .h5 output into netcdf, on a regular latlon grid,
    for the following variables:
    - SWdown, SWup, LWdown LWup,
    - QH, QE, QS, QF
    - T2, TS, RH2, Q2, U10
    - RO, TotCh, SMD
    - LAI, AlbBulk
    - ustar, zdm, z0m,
    """
    # Get the parent directory of the input file
    fn_base = Path(input_file).parent.parent.parent
    # Get the input file name
    fn_in = Path(input_file)
    # Check if the input file name starts with 'df_output'
    if not fn_in.name.startswith('df_output'):
        raise ValueError("Invalid input file name. Please make sure the file name starts with 'df_output'.")
    # Set the output file name with the same name as the input file but with .nc extension
    fn_out_nc = fn_in.with_suffix('.nc')
    # Set the output file name with the same name as the input file but with '_latlon.nc' extension
    fn_out_latlon_nc = fn_in.with_name(fn_in.stem + '_latlon.nc')
    # Set the path to the grid shapefile
    fn_grid_shp = fn_base / 'input' / 'grid' / 'roi_grid.shp'

    # Read SUEWS OUTPUT
    df = pd.read_hdf(input_file)

    # Initizalise dataframe to store grid coordinates
    grid = gpd.read_file(fn_grid_shp)
    df_xy = pd.DataFrame(
        index=grid.index,
        columns=['longitude', 'latitude'],
    )

    # Use the original projection (UTM) that is defined in meters
    # This info is available from arguments of the tool, and follows:
    # https://github.com/matthiasdemuzere/supy-lcz-global/blob/11dfcadfc4aefb66d32c6564f2646845bd2d6b01/runner/utils.py#L86
    crs_dict = {
        'proj': 'utm',
        'zone': int(np.round((183 + lon) / 6)),
        'south': lat < 0,
    }
    crs = CRS.from_dict(crs_dict)
    to_utm = Transformer.from_crs(crs_from='EPSG:4326', crs_to=crs)
    x_m, y_m = to_utm.transform(xx=lat, yy=lon)

    # Derive nx from the number of grid cells
    nx = int(np.sqrt(grid.index.size))

    # Calculate the maximum and minimum values of x and y
    y_m_max = y_m + (nx / 2 * dx)
    y_m_min = y_m_max - ((nx - 1) * dx)
    x_m_max = x_m + (nx / 2 * dx)
    x_m_min = x_m_max - ((nx - 1) * dx)

    # Create arrays of x and y coordinates
    y_m = np.linspace(y_m_min, y_m_max, nx)
    x_m = np.linspace(x_m_min, x_m_max, nx)
    xx, yy = np.meshgrid(y_m, x_m)

    # Store the x and y coordinates in the dataframe
    df_xy['longitude'] = xx.flatten()
    df_xy['latitude'] = yy.flatten()

    # Convert multi-index to columns
    df['grid'] = df.index.get_level_values(0)
    df['time'] = df.index.get_level_values(1)

    # Set grid id number as only index
    df = df.droplevel(1)

    # Join SUEWS output with coordinates
    df_new = df.join(df_xy)

    # Select variables of interest
    vars = ['time', 'latitude', 'longitude',
            'Kdown', 'Kup', 'Ldown', 'Lup',
            'QN', 'QH', 'QE', 'QS', 'QF',
            'T2', 'Ts', 'RH2', 'Q2', 'U10',
            'RO', 'TotCh', 'SMD'
            ]

    # Convert to xarray dataframe and clean
    print("Converting to xarray dataframe and cleaning ...")
    ds = df_new[vars].set_index(['time', 'latitude', 'longitude']).to_xarray()
    ds = ds.sortby(["time", "latitude", "longitude"])
    ds.rio.write_crs(crs, inplace=True)
    print("Writing to netcdf file ...")
    ds.to_netcdf(fn_out_nc)
    print("Output saved to", fn_out_nc)

    # Convert output also to lat lon
    print("Converting output to in regular lat-lon format ...")
    ds_lonlat = ds.rio.reproject("EPSG:4326")
    ds_lonlat.to_netcdf(fn_out_latlon_nc)
    print("Output converted to lat lon and saved to", fn_out_latlon_nc)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Convert .h5 output to netcdf.')
    parser.add_argument('input_file', type=str, help='Path to input .h5 file')
    # parser.add_argument('--nx', type=int, required=True, help='Number of grid cells in x direction')
    parser.add_argument('--dx', type=int, required=True, help='Grid cell size in meters')
    parser.add_argument('--lat', type=float, required=True, help='Latitude of the grid center')
    parser.add_argument('--lon', type=float, required=True, help='Longitude of the grid center')
    args = parser.parse_args()

    convert_h5_to_netcdf(args.input_file, args.dx, args.lat, args.lon)
    # Convert .h5 output to netcdf
    # Example usage: python structure_grid_output.py /path/to/input.h5 --nx 100 --dx 100 --lat 40.7128 --lon -74.0060

