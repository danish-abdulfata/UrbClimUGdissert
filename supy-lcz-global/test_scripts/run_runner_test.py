import os
os.environ['USE_PYGEOS'] = '0'

import time
import argparse
from pathlib import Path
from runner.runner import main as run_supy

############################# Testing for run_split_models.py, 2nd part.

split_runs_start = time.time()

site_list = ['KL-KualaLumpurTest1', 'KL-KualaLumpurTest2', 'KL-KualaLumpurTest3']

number_of_runs = 3

split_run_count = 0
for individual_split_site in site_list:
    run_supy([individual_split_site,
        '--run-type', 'grid',
        '--grid-size', '1000',
        '--grid-boxes', '20',
        '--metforc-src', 'era5land',
        '--urbdesc-src', 'lcz_updated',
        '--sitelist', 'sitelist_custom',
        '--download-era5'])
    split_run_count += 1
    print(f"====> Split Run #{split_run_count} completed out of {number_of_runs} for {individual_split_run}") 
    print(f"====> Split Run {individual_split_site} completed out of {number_of_runs} for site_name_prefix") 
        
split_runs_end = time.time()
print(f"==============> Total runtime: {(split_runs_end - split_runs_start):.2f} s <=================")