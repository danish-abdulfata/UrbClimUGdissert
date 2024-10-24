import pandas as pd
import supy
from pathlib import Path
import matplotlib.pyplot as plt
import traceback

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
        print(city)

        site_info = get_city_from_site_list(city)

        # Read ERA5
        fn_era5 = Path('data', site_info['sitename'], 'input', 'era5')
        era5_forcings = sorted(fn_era5.glob('ERA5_*_data_60.txt'))
        df_era5_forcing = pd.concat(
            [supy.util.read_forcing(
                f,
                tstep_mod=site_info['timestep_interval_seconds']
            ) for f in era5_forcings]
        )
        df_era5_forcing = supy.check_forcing(df_era5_forcing, fix=True)

        # Read ERA5LAND
        fn_era5 = Path('data', site_info['sitename'], 'input', 'era5land')
        era5_forcings = sorted(fn_era5.glob('ERA5LAND_*_data_60.txt'))
        df_era5land_forcing = pd.concat(
            [supy.util.read_forcing(
                f,
                tstep_mod=site_info['timestep_interval_seconds']
            ) for f in era5_forcings]
        )
        df_era5land_forcing = supy.check_forcing(df_era5land_forcing, fix=True)

        # Clip to analysis period
        start = site_info['time_coverage_start']
        start_analysis = site_info['time_analysis_start']
        end = site_info['time_coverage_end']

        df_era5_forcing = df_era5_forcing.loc[start_analysis:end]
        df_era5land_forcing = df_era5land_forcing.loc[start_analysis:end]

        df_era5_forcing['U'].plot()
        df_era5land_forcing['U'].plot()


        # Make a plot showing full timeseries as scatter, and average diurnal cycle?
        vars = ['kdown', 'ldown','U', 'RH', 'Tair', 'pres', 'rain',  'snow']

        fig, ax = plt.subplots(2,len(vars), figsize=(25,10))

        for v, var in enumerate(vars):

            # Panel 1: scatter plot
            ax[0,v].scatter(df_era5_forcing[var],df_era5land_forcing[var] )
            ax[0, v].set_title(var)

            # Panel 2: mean diurnal cycle
            df_era5_forcing.groupby(['it', 'imin']).mean()[var].plot(ax=ax[1,v], label="ERA5")
            df_era5land_forcing.groupby(['it', 'imin']).mean()[var].plot(ax=ax[1, v], label="ERA5LAND")
            ax[1,0].legend()

        plt.tight_layout()
        figfile = f"/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/figs/{city}_compare_era5_era5land.png"
        plt.savefig(figfile)
        plt.close("all")

    except Exception:
        print(f"ERROR for {city}:\n")
        print(traceback.format_exc())
