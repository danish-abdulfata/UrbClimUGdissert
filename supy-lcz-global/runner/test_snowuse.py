import supy
import os
import argparse
import pandas as pd
from pathlib import Path
from utils import store_output_h5
#from runner.utils import store_output_nc

#site = 'US-Minneapolis2'
#site = 'FI-Torni'

sites = ['US-Minneapolis1', 'US-Minneapolis2', 'FI-Torni', 'FI-Kumpula', 'UK-Swindon',]
sites = ['CA-Sunset','KR-Ochang', 'KR-Jungnang', 'JP-Yoyogi', 'GR-HECKOR']

#sites = ['US-Minneapolis1']

#sim_code = "sMF_sLC"
sim_code = "uMF_uLCu"

def get_city_from_site_list(args: argparse.Namespace) -> pd.Series:

    # check if a custom sitelist was set and read it
    if args.sitelist is not None:
        fn_sitelist = args.sitelist
    else:
        fn_sitelist = 'sitelist_urbanplumber'

    site_list = pd.read_csv(f'resources/{fn_sitelist}.csv')
    # this should always only be a one row df!
    return site_list[site_list['sitename'] == args.city].iloc[0]


for site in sites:
    class args:
        city = site
        run_type = 'buffer'
        sitelist = None

    site_info = get_city_from_site_list(args)

    # check the machine you are working on
    nodename = os.uname().nodename

    if nodename == 'rub-gis16':
        fn_base = Path("/home/demuzmp4/scripts/supy-lcz-global/data")
    else:
        fn_base = Path("/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/data")

    # Test dir
    fn_dir = fn_base / "tests" / "snowuse" / f"{site}"

    # Get the forcing data
    fn_state = fn_dir / f"df_state_final_{sim_code}.pkl"
    fn_forcing = fn_dir / f"df_final_forcing_{sim_code}.h5"

    df_state = pd.read_pickle(fn_state)

    df_state_init = pd.DataFrame(df_state.iloc[0]).T
    df_state_init = df_state_init.droplevel(0)
    df_state_init.index.name = 'grid'

    # df_state_init = pd.DataFrame(df_state.iloc[1]).T
    # startdate = df_state_init.index.droplevel(1)
    # df_state_init = df_state_init.droplevel(0)
    # df_state_init.index.name = 'grid'

    df_forcing = pd.read_hdf(fn_forcing)
    # if not full_spinup:
    #     df_forcing = df_forcing.loc[startdate[0]:]

    # Test with snow use
    df_state_init.snowuse=1
    print(df_state_init.snowuse)

    # Run the model
    print(f"*** Execute simulation for {site} ****")
    df_output, df_state_final = supy.run_supy(
        df_forcing=df_forcing,
        df_state_init=df_state_init,
    )

    # Store the output
    freq_out = int(site_info['timestep_interval_seconds'] / 60)
    suews_output_file = fn_dir / f"df_output_{sim_code}_snow.h5"
    store_output_h5(df_output, site_info, suews_output_file, freq_out)

    # Store final state
    final_state_file = fn_dir / f'df_state_final_{sim_code}_snow.pkl'
    df_state_final.to_pickle(final_state_file)

# sim_code = 'sMF_sLC'
# suews_output_file_up = output_path / "df_output_sMF_sLC_snow.nc"
# store_output_nc(args, site_info, sim_code, suews_output_file_up)
# print(f'==> output converted to Urban Plumber format')