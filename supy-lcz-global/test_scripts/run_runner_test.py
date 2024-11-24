import time
from pathlib import Path
from runner.runner import main as run_runner

############################# Testing for run_split_models.py, 2nd part.

split_runs_start = time.time()
site_list = ['KL-KualaLumpur-2016_1month_s1', 'KL-KualaLumpur-2016_1month_s2']
# , 'KL-KualaLumpur-2016_1month_s3', 'KL-KualaLumpur-2016_1month_s4'
number_of_runs = 3
split_grid_length = 5
split_run_count = 0
site_prefix = "KL-KualaLumpur-2016"

for individual_split_site in site_list:
    run_runner([individual_split_site,
        '--run-type', 'grid',
        '--grid-size', '1000',
        '--grid-boxes', str(split_grid_length),
        '--metforc-src', 'era5land',
        '--urbdesc-src', 'lcz_updated',
        '--sitelist', f'{site_prefix}_splitlist',
        '--download-era5',
        '--do-spinup'])
    split_run_count += 1
    print(f"====> Split Run #{split_run_count} completed out of {number_of_runs} for {individual_split_site}") 
    print(f"====> Split Run {individual_split_site} completed out of {number_of_runs} for site_name_prefix") 
        
split_runs_end = time.time()
print(f"==============> Total runtime: {(split_runs_end - split_runs_start):.2f} s <=================")