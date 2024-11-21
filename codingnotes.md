### Model and Coding Notes

```
micromamba env installtion failure: 
warning  libmamba You are using 'pip' as an additional package manager.
    Be aware that packages installed with 'pip' are managed independently from 'conda-forge' channel.

Installing pip packages: supy==2024.7.12.dev0
'"C:\Users\Danish\micromamba\condabin\micromamba"' is not recognized as an internal or external command,
operable program or batch file.
critical libmamba pip failed to install packages
```

testing `python -m pip install supy` - works!

USE mklink for Windows
`mklink /d C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global\data "C:\Users\Danish\OneDrive - University College London\dissertation_data\lcz-supy-global-data"`

Git Subtree commandline
`git subtree add --prefix C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global\ https://github.com/UrbanClimateRisk-UCL/supy-lcz-global main --squash`

Git Overleaf Update
`git submodule update --remote --merge`

AFTER RUNNING PUSH LCOAL REPO TO MAIN.

MODEL RUN TESTING

FIRST RUN: 
python -m runner.runner KL-KualaLumpurTest --run-type grid --grid-size 1000 --grid-boxes 20 --metforc-src era5land --urbdesc-src lcz_updated --sitelist sitelist_custom --download-era5

python -m test_scripts.structure_grid_output C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global\data\KL-KualaLumpurTest\output\grid\df_output_uMF_uLCu.h5 --dx 1000 --lat 3.056577 --lon 101.617373

python -m runner.runner KL-KualaLumpurTest1 --run-type grid --grid-size 1000 --grid-boxes 20 --metforc-src era5land --urbdesc-src lcz_updated --sitelist sitelist_custom --download-era5

wslpath 

cd /mnt/c/Users/Danish/Documents/GitHub/UrbClimUGdissert/supy-lcz-global
micromamba activate supy_lcz

python -m test_scripts.structure_grid_output /mnt/c/Users/Danish/Documents/GitHub/UrbClimUGdissert/supy-lcz-global/data/KL-KualaLumpurTest/output/grid/df_output_uMF_uLCu.h5 --dx 1000 --lat 3.056577 --lon 101.617373

python -m runner.runner KL-KualaLumpurTest5 --run-type grid --grid-size 1000 --grid-boxes 40 --metforc-src era5land --urbdesc-src lcz_updated --sitelist sitelist_custom --download-era5

python -m test_scripts.run_runner_test

python -m test_scripts.run_split_models



python -m runner.runner KL-KualaLumpur-2016_1month_s1 --run-type grid --grid-size 1000 --grid-boxes 5 --metforc-src era5land --urbdesc-src lcz_updated --sitelist KL-KualaLumpur-2016_1month_splitlist_custom --download-era5