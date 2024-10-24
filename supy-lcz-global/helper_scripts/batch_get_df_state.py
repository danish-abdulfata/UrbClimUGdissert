import os
import pandas as pd

site_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
sites = list(site_list['sitename'].values)
sites = ['NL-Amsterdam']
sites = ['GR-HECKOR']

up_descriptions =  [
    'up_baseline',
    'up_detailed',
    'lcz_default',
    'lcz_updated',
]

for site in sites:

    for up_descr in up_descriptions:
        
        #site = 'FI-Torni'; up_descr = 'lcz_updated'

        #print(f" ************** {site} | {up_descr} ************** ")

        cmd = f"python -m runner.runner " \
              f"{site} --run-type buffer " \
              f"--metforc-src era5 " \
              f"--urbdesc-src {up_descr} " \
              f"--initialize-only"

        os.system(cmd)

# # For one combination only
# site = 'AU-SurreyHills'; up_descr = 'lcz_updated'
# site = 'FI-Kumpula'; up_descr = 'lcz_updated'
# site = 'FI-Torni'; up_descr = 'lcz_updated'
# site = 'GR-HECKOR'; up_descr = 'lcz_updated'
# site = 'KR-Ochang'; up_descr = 'lcz_updated'
# site = 'NL-Amsterdam'; up_descr = 'lcz_updated'
# site = 'SG-TelokKurau06'; up_descr = 'lcz_updated'
# site = 'US-Baltimore'; up_descr = 'lcz_updated'
# site = 'US-Minneapolis1'; up_descr = 'lcz_updated'
# site = 'US-Minneapolis2'; up_descr = 'lcz_updated'
# cmd = f"python -m runner.runner " \
#       f"{site} --run-type buffer " \
#       f"--metforc-src era5 " \
#       f"--urbdesc-src {up_descr} " \
#       f"--initialize-only"
#
# os.system(cmd)