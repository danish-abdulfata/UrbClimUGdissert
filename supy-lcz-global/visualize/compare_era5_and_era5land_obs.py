import pandas as pd
import supy
from pathlib import Path
import matplotlib.pyplot as plt
import traceback
from datetime import datetime, timedelta

fn_data = '/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/data'

def get_city_from_site_list(city: str) -> pd.Series:
    site_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
    # this should always only be a one row df!
    return site_list[site_list['sitename'] == city].iloc[0]

city_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
cities = list(city_list['sitename'].values);

#cities = ['CA-Sunset', 'FI-Kumpula', 'FI-Torni', 'PL-Lipowa', 'PL-Narutowicza',]

for city in cities:

    # Surrey ERA5 misses the last timestep [2004-07-19 23:30:00]?
    # CA-Sunset: supy read forcing:  index 1 is out of bounds for axis 0 with size 1?
    # FI-Kumpula: supy read forcing:  index 1 is out of bounds for axis 0 with size 1?

    try:

        #city = "AU-Preston"
        # city = "AU-SurreyHills"
        #city = "CA-Sunset"
        # city = "FI-Kumpula"
        # city = "FI-Torni"
        #city = "PL-Lipowa"
        # city = "PL-Narutowicza"
        #city = "US-Baltimore"
        #city = "US-Minneapolis1"
        # city = "US-Minneapolis2"
        # city = "US-WestPhoenix"
        print(city)

        site_info = get_city_from_site_list(city)

        # Read the UP obs forcing
        fn_up = Path('data', site_info['sitename'], 'input')
        up_forcings = sorted(fn_up.glob(f'{city}_*_data.txt'))
        df_up_forcing = pd.concat(
            [supy.util.read_forcing(
                f,
                tstep_mod=site_info['timestep_interval_seconds']
            ) for f in up_forcings]
        )
        df_up_forcing = supy.check_forcing(df_up_forcing, fix=True)


        # Read ERA5 - Adjust to Local time to match UP obs
        fn_era5 = Path('data', site_info['sitename'], 'input', 'era5')
        era5_forcings = sorted(fn_era5.glob('ERA5_*_data_60.txt'))
        df_era5_forcing = pd.concat(
            [supy.util.read_forcing(
                f,
                tstep_mod=site_info['timestep_interval_seconds']
            ) for f in era5_forcings]
        )
        df_era5_forcing.index = df_era5_forcing.index + \
                                timedelta(hours=int(site_info['local_utc_offset_hours']))
        df_era5_forcing['iy'] = df_era5_forcing.index.year
        df_era5_forcing['id'] = df_era5_forcing.index.dayofyear
        df_era5_forcing['it'] = df_era5_forcing.index.hour
        df_era5_forcing['imin'] = df_era5_forcing.index.minute
        df_era5_forcing['isec'] = df_era5_forcing.index.second
        df_era5_forcing = supy.check_forcing(df_era5_forcing, fix=True)

        # # Read ERA5LAND
        # fn_era5 = Path('data', site_info['sitename'], 'input', 'era5land')
        # era5_forcings = sorted(fn_era5.glob('ERA5LAND_*_data_60.txt'))
        # df_era5land_forcing = pd.concat(
        #     [supy.util.read_forcing(
        #         f,
        #         tstep_mod=site_info['timestep_interval_seconds']
        #     ) for f in era5_forcings]
        # )
        # df_era5land_forcing.index = df_era5land_forcing.index + \
        #                         timedelta(hours=int(site_info['local_utc_offset_hours']))
        # df_era5land_forcing['iy'] = df_era5land_forcing.index.year
        # df_era5land_forcing['id'] = df_era5land_forcing.index.dayofyear
        # df_era5land_forcing['it'] = df_era5land_forcing.index.hour
        # df_era5land_forcing['imin'] = df_era5land_forcing.index.minute
        # df_era5land_forcing['isec'] = df_era5land_forcing.index.second
        # df_era5land_forcing = supy.check_forcing(df_era5land_forcing, fix=True)

        # Read ERA5LAND - Diagnosed
        fn_era5 = Path('data', site_info['sitename'], 'input', 'era5land')
        era5_forcings = sorted(fn_era5.glob('ERA5LAND_*_data_60.txt'))
        df_era5land_diag_forcing = pd.concat(
            [supy.util.read_forcing(
                f,
                tstep_mod=site_info['timestep_interval_seconds']
            ) for f in era5_forcings]
        )
        df_era5land_diag_forcing.index = df_era5land_diag_forcing.index + \
                                timedelta(hours=int(site_info['local_utc_offset_hours']))
        df_era5land_diag_forcing['iy'] = df_era5land_diag_forcing.index.year
        df_era5land_diag_forcing['id'] = df_era5land_diag_forcing.index.dayofyear
        df_era5land_diag_forcing['it'] = df_era5land_diag_forcing.index.hour
        df_era5land_diag_forcing['imin'] = df_era5land_diag_forcing.index.minute
        df_era5land_diag_forcing['isec'] = df_era5land_diag_forcing.index.second
        df_era5land_diag_forcing = supy.check_forcing(df_era5land_diag_forcing, fix=True)

        # Clip to analysis period
        start = site_info['time_coverage_start']
        start_analysis = pd.to_datetime(site_info['time_analysis_start']) + \
                                timedelta(hours=int(site_info['local_utc_offset_hours']))
        end = pd.to_datetime(site_info['time_coverage_end']) + \
                                timedelta(hours=int(site_info['local_utc_offset_hours']))

        df_up_forcing = df_up_forcing.loc[start_analysis:end]
        df_era5_forcing = df_era5_forcing.loc[start_analysis:end]
        #df_era5land_forcing = df_era5land_forcing.loc[start_analysis:end]
        df_era5land_diag_forcing = df_era5land_diag_forcing.loc[start_analysis:end]

        # Make a plot showing full timeseries as scatter, and average diurnal cycle?
        vars = ['kdown', 'ldown','U', 'RH', 'Tair', 'pres', 'rain']

        fig, ax = plt.subplots(2,len(vars), figsize=(25,10))

        for v, var in enumerate(vars):

            # Panel 1: scatter plot
            ax[0, v].scatter(df_up_forcing[var], df_era5_forcing[var],
                             s=10, label="ERA5", color="#beaed4")
            #ax[0, v].scatter(df_up_forcing[var], df_era5land_forcing[var],
            #                 s=10, label="ERA5LAND", color="#7fc97f")
            ax[0, v].scatter(df_up_forcing[var], df_era5land_diag_forcing[var],
                             s=10, label="ERA5LAND", color="#fdc086")
            ax[0, 0].legend()
            ax[0, v].set_title(var)
            ax[0, v].set_xlabel("obs")
            ax[0, 0].set_ylabel("ERA5")

            # Panel 2: mean diurnal cycle
            df_era5_forcing.groupby(['it', 'imin']).mean()[var].plot(ax=ax[1, v], label="ERA5", color="#beaed4")
            #df_era5land_forcing.groupby(['it', 'imin']).mean()[var].plot(ax=ax[1, v], label="ERA5LAND", color="#7fc97f")
            df_era5land_diag_forcing.groupby(['it', 'imin']).mean()[var].plot(ax=ax[1, v], label="ERA5LAND", color="#fdc086")
            df_up_forcing.groupby(['it', 'imin']).mean()[var].plot(ls=":", color="0.2", ax=ax[1, v], label="Obs")
            ax[1,0].legend()

        plt.tight_layout()
        figfile = f"/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/figs/{city}_compare_era5_era5land_obs.png"
        plt.savefig(figfile)
        plt.close("all")

    except Exception:
        print(f"ERROR for {city}:\n")
        print(traceback.format_exc())
