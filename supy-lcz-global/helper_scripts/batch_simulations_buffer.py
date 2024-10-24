import os
import itertools
import pandas as pd

# check the machine you are working on
nodename = os.uname().nodename

if nodename == 'rub-gis16':
    fn_dir = "/home/demuzmp4/scripts/supy-lcz-global/data"
else:
    fn_dir = "/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/data"

site_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
cities = site_list['sitename'].values

meteos = ['obs', 'era5land']
ups = ['up_detailed', 'lcz_updated']

#for city in cities:
#cities = ["US-WestPhoenix", "FI-Torni", "AU-Preston"]
#city = "FI-Torni"
#city = "SG-TelokKurau06"

for city in cities:

    for exp in itertools.product(meteos, ups):

        if exp[0] == 'obs':
            # Forcing as provided by UP, based on flux tower observations
            mf_value = 'sMF'
        else:
            mf_value = 'uMF'

        if exp[1] == 'up_detailed':
            # Forcing as provided by UP, based on flux tower observations
            ud_value = 'sLC'
        else:
            ud_value = 'uLCu'

        sim_code = f'{mf_value}_{ud_value}'

        # Check if .nc output is available.
        # If so, skip this iteration
        out_file = os.path.join(
            fn_dir,
            city,
            'output',
            'buffer',
            f"output_{sim_code}.nc"
        )

        if not os.path.exists(out_file):
            log_file = os.path.join(
                fn_dir,
                'logs',
                f"SuPy_Buffer_{city}_{sim_code}.log"
            )

            cmd = f"python -m runner.runner {city} " \
                  f"--run-type buffer " \
                  f"--metforc-src {exp[0]} " \
                  f"--urbdesc-src {exp[1]} " \
                  f"2>&1 | tee {log_file}"

            print(f"Executing: {cmd}")

            # Launch
            os.system(cmd)

        else:
            print(f" >>> {city} - {sim_code} already available.")

