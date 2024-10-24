import pandas as pd
import supy
from pathlib import Path
import matplotlib.pyplot as plt
import traceback
from atmosp import calculate as ac
import numpy as np

fn_data = '/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/data'

def get_city_from_site_list(city: str) -> pd.Series:
    site_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
    # this should always only be a one row df!
    return site_list[site_list['sitename'] == city].iloc[0]

def _era5land_get_z0m(lon_new, lat_new):

    ''' Get appropriate z0m value for selected land pixel '''

    # Read the vegetation type and cover files
    fn_tvl = 'resources/tvl.nc'
    fn_tvh = 'resources/tvh.nc'
    fn_cvl = 'resources/cvl.nc'
    fn_cvh = 'resources/cvh.nc'

    #xarray.open_mfdataset failed because of different timestamp?
    ds_tvl = xr.open_dataset(fn_tvl).squeeze(dim='time')
    ds_tvh = xr.open_dataset(fn_tvh).squeeze(dim='time')
    ds_cvl = xr.open_dataset(fn_cvl).squeeze(dim='time')
    ds_cvh = xr.open_dataset(fn_cvh).squeeze(dim='time')

    # Combine
    dsv = xr.merge([ds_tvl, ds_tvh, ds_cvl, ds_cvh], compat='override')

    # Make longitudes consistent with sitelist [-180 to 180]
    # instead of [0 to 306]
    dsv.coords['longitude'] = (dsv.coords['longitude'] + 180) % 360 - 180
    dsv = dsv.sortby(ds['longitude'])

    # Get values for pixel
    dsv_point = dsv.sel(
        longitude=lon_new,
        latitude=lat_new,
        method="nearest"
    )

    # Read look-up table for vegetation characteristics
    veg_table = pd.read_csv('resources/ECMWF_IFS_VegetationProperties.csv', index_col=0)

    # get the fractions, as Eq. 8.1 in documentation, and
    # corresponding z0m, based on Eq. 8.5
    if int(np.ceil(dsv_point.tvh.values)) != 0:
        c_veg_h = veg_table.loc[int(np.round(dsv_point.tvh.values, 0)), 'c_veg']
        c_h = float(dsv_point.cvh.values) * c_veg_h
        z0m_c_h = c_h / (np.log(10) / veg_table.loc[int(np.ceil(dsv_point.tvh.values)), 'z0_m']) ** 2
    else:
        z0m_c_h = 0.0

    if int(np.round(dsv_point.tvl.values, 0)) != 0:
        c_veg_l = veg_table.loc[int(np.round(dsv_point.tvl.values, 0)), 'c_veg']
        c_l = float(dsv_point.cvl.values) * c_veg_l
        z0m_c_l = c_l / (np.log(10) / veg_table.loc[int(np.ceil(dsv_point.tvl.values)), 'z0_m']) ** 2
    else:
        z0m_c_l = 0.0

    # aggregated roughness length
    sum_z0m = z0m_c_h + z0m_c_l
    z0ma = (sum_z0m * np.log(10)**2)**0.5

    return z0ma

def era5land_check_lsm(site_info, dir_save):

    '''
    Check if the coordinates will contain data, as ERA5-Land has no data
    for pixels with land fraction < 50%:

    Data: https://confluence.ecmwf.int/display/CKB/ERA5-Land%3A+data+documentation
    '''

    # Get the pixel value
    fn_lsm = 'resources/lsm_1279l4_0.1x0.1.grb_v4_unpack.nc'
    ds = xr.open_dataset(fn_lsm)

    # Make longitudes consistent with sitelist [-180 to 180]
    # instead of [0 to 306]
    ds.coords['longitude'] = (ds.coords['longitude'] + 180) % 360 - 180
    ds = ds.sortby(ds['longitude'])

    ds_point = ds.sel(
        longitude=site_info['longitude'],
        latitude=site_info['latitude'],
        method="nearest"
    )
    max_value = float(ds_point.lsm.data)

    # if lsm is < 0.5, check 8 neighbouring pixels, take one with highest lsm value
    if max_value <= 0.5:

        print("     |- Not enough landmass at this coordinate, "
              "looking at neighbouring pixels")

        dxy = 0.15
        dxy_iter = 0

        # Check surroundings pixels with a window.
        # Continue to check as long as no valid pixels are found
        while max_value <= 0.5:

            dxy_iter += 1

            ds_window = ds.sel(
                longitude=slice(
                    (site_info['longitude']-(dxy_iter*dxy)),
                    (site_info['longitude']+(dxy_iter*dxy))
                ),
                latitude=slice(
                    (site_info['latitude']+(dxy_iter*dxy)),
                    (site_info['latitude']-(dxy_iter*dxy))
                ),
            )
            max_value = ds_window.lsm.max()

        # Get the coordinates of this max value pixel
        lon_new = float(ds_window.where(
            ds_window == max_value, drop=True
        ).squeeze().longitude)
        lat_new = float(ds_window.where(
            ds_window == max_value, drop=True
        ).squeeze().latitude)

        print(f"     |- Valid neighbouring pixel found in "
              f"{dxy_iter} iteration(s): "
              f"lat = {np.round(lon_new,4)}, "
              f"lon = {np.round(lat_new,4)}, "
              f"lsm = {np.round(float(max_value),4)}"
              )

    else:
        # Keep original coordinates
        print("     |- Selected pixel is valid.")
        lon_new = site_info['longitude']
        lat_new = site_info['latitude']

    # Write info to file
    path_note = dir_save / "ERA5-Land_Note_on_coordinates"
    f = open(path_note, "a")
    line_old = f"Original pixel (lon | lat | land fraction): " \
               f"{site_info['longitude']} | {site_info['latitude']} | " \
               f"{float(ds_point.lsm)}"
    line_new = f"New pixel (lon | lat | land fraction): " \
               f"{lon_new} | {lat_new} | {float(max_value)}"
    f.writelines([f"\n{line_old}",f"\n{line_new}"])
    f.close()

    return lon_new, lat_new

def _diag_era5land(z0m, pres_z0, uv10, t2, q2, z):

    # constants
    # environmental lapse rate [K m^-1]
    env_lapse = 6.5 / 1000.0
    # gravity [m s^-2]
    grav = 9.80616
    # Gas constant for dry air [J K^-1 kg^-1]
    rd = 287.04

    # correct temperature using lapse rate
    t_z = t2 - (z - 2) * env_lapse

    # barometric equation with varying temperature:
    # (https://en.wikipedia.org/wiki/Barometric_formula)
    p_z = pres_z0 * (t_z / t2) ** (grav / (rd * env_lapse))

    # correct humidity assuming invariable relative humidity
    RH_z = ac("RH", qv=q2, p=pres_z0, T=t2) + 0 * t_z
    #q_z = ac("qv", RH=RH_z, p=p_z, T=t_z) + 0 * t_z

    # correct wind speed using log law; assuming neutral condition (without stability correction)
    uv_z = uv10 * (np.log((z + z0m) / z0m) / np.log((10 + z0m) / z0m))

    return uv_z, t_z, RH_z, p_z # q_z

def format_era5land_forcing(site_info, lon_new, lat_new, dir_save, hgt_agl_diag=100):

    era5land_forcings = sorted(dir_save.glob('ERA5LAND_*.csv'))
    df_forcing = pd.concat(
        pd.read_csv(f, index_col=0, parse_dates=True)
        for f in era5land_forcings
    )

    df_forcing_format = df_forcing.copy()

    # Get the aggregated surface roughness [m]
    z0m = _era5land_get_z0m(lon_new, lat_new)
    print(f"    -----> z0m: {z0m}")

    # Prepare all for diagnostics at height hgt_agl_diag=100 m (default)
    # surface level atmospheric pressure
    pres_z0 = df_forcing_format.pres

    # wind speed
    u10 = df_forcing_format.u10m
    v10 = df_forcing_format.v10m
    uv10 = np.sqrt(u10**2 + v10**2)

    # air temperature
    t2 = df_forcing_format.Tair

    # dew point
    d2 = df_forcing_format.Td

    # specific humidity
    q2 = ac("qv", Td=d2, T=t2, p=pres_z0)

    # Diagnose the properties
    uv_z, t_z, RH_z, p_z = _diag_era5land(
        z0m=z0m,
        pres_z0=pres_z0,
        uv10=uv10,
        t2=t2,
        q2=q2,
        z=hgt_agl_diag,
    )

    # Put diagnosed into in dataframe, adjust existing columns
    # Mean wind speed U
    df_forcing_format.loc[:, "U"] = uv_z
    df_forcing_format.drop(['u10m', 'v10m'], axis=1, inplace=True)

    # convert energy fluxes: [J m-2] to [W m-2]
    #df_forcing_format.loc[:, ["kdown", "ldown", "qh", "qe"]] /= 3600
    df_forcing_format.loc[:, ["kdown", "ldown"]] /= 3600

    # reverse the sign of qh and qe
    #df_forcing_format.loc[:, ["qh", "qe"]] *= -1

    # convert rainfall: from [m] to [mm]
    df_forcing_format.loc[:, "rain"] *= 1000

    # Set diagnosed bulb temperature in degC
    df_forcing_format.loc[:, "Tair"] = t_z - 273.15

    # Set diagnosed relative humidity
    df_forcing_format.loc[:, "RH"] = RH_z
    df_forcing_format.drop(['Td'], axis=1, inplace=True)

    # convert diagnosed pressure: [Pa] to [kPa]
    df_forcing_format.loc[:, "pres"] = p_z / 1000

    dict_var_type_forcing = {
        "iy": "time",
        "id": "time",
        "it": "time",
        "imin": "time",
        "qn": "avg",
        "qh": "avg",
        "qe": "avg",
        "qs": "avg",
        "qf": "avg",
        "U": "inst",
        "RH": "inst",
        "Tair": "inst",
        "pres": "inst",
        "rain": "sum",
        "kdown": "avg",
        "snow": "inst",
        "ldown": "avg",
        "fcld": "inst",
        "Wuh": "sum",
        "xsmd": "inst",
        "lai": "inst",
        "kdiff": "avg",
        "kdir": "avg",
        "wdir": "inst",
        "isec": "time",
    }

    col_suews = list(dict_var_type_forcing.keys())[:-1]

    df_forcing_format = df_forcing_format.reindex(col_suews, axis=1)

    df_forcing_format = df_forcing_format.assign(
        iy=df_forcing_format.index.year,
        id=df_forcing_format.index.dayofyear,
        it=df_forcing_format.index.hour,
        imin=df_forcing_format.index.minute,
    )

    # corrections
    df_forcing_format.loc[:, "RH"] = df_forcing_format.loc[:, "RH"].where(
        df_forcing_format.loc[:, "RH"].between(0.001, 105), 105
    )
    df_forcing_format.loc[:, "kdown"] = df_forcing_format.loc[:, "kdown"].where(
        df_forcing_format.loc[:, "kdown"] > 0, 0
    )

    # trim decimals
    df_forcing_format.iloc[:, 4:] = df_forcing_format.iloc[:, 4:].round(2)

    # coerce integer
    df_forcing_format = df_forcing_format.astype(
        {"iy": "int32", "id": "int32", "it": "int32", "imin": "int32"}
    )

    # Remove duplicate timestamps
    df_forcing_format = df_forcing_format[~df_forcing_format.index.duplicated(keep='first')]

    # replace nan with -999
    df_forcing_format = df_forcing_format.replace(np.nan, -999).asfreq("1h")

    # split into years
    idx_grid = df_forcing_format.index
    grp_year = df_forcing_format.groupby(idx_grid.year)

    lat = site_info['latitude']
    lon = site_info['longitude']
    s_lat = f"{lat}N" if lat >= 0 else f"{-lat}S"
    s_lon = f"{lon}E" if lon >= 0 else f"{-lon}W"

    for year in grp_year.groups:
        df_year = grp_year.get_group(year)
        idx_year = df_year.index
        s_year = idx_year[0].year
        s_freq = idx_year.freq / pd.Timedelta("1T")
        s_fn = f"ERA5LAND_UTC-{s_lat}-{s_lon}_{s_year}_data_{s_freq:.0f}.txt"
        path_fn = dir_save / s_fn
        df_year.to_csv(path_fn, sep=" ", index=False)

city_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
cities = list(city_list['sitename'].values);

#cities = ["AU-Preston"]
#cities = ["PL-Lipowa"]

for city in cities:

    #city = "AU-Preston"
    #city = "JP-Yoyogi"
    #city = "US-Baltimore"
    print(city)
    site_info = get_city_from_site_list(city)

    dir_save = Path('data', site_info['sitename'], 'input', 'era5land')
    lon_new, lat_new = era5land_check_lsm(site_info, dir_save)
    format_era5land_forcing(site_info, lon_new, lat_new, dir_save)