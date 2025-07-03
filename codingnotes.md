### Model and Coding Notes

USE mklink for Windows
`mklink /d C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global\data "C:\Users\Danish\OneDrive - University College London\dissertation_data\lcz-supy-global-data"`

Git Subtree commandline
`git subtree add --prefix C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global\ https://github.com/UrbanClimateRisk-UCL/supy-lcz-global main --squash`

Git Overleaf Update
`git submodule update --remote --merge`

cd /mnt/c/Users/Danish/Documents/GitHub/UrbClimUGdissert/supy-lcz-global
micromamba activate supy_lcz

python -m test_scripts.structure_grid_output /mnt/c/Users/Danish/Documents/GitHub/UrbClimUGdissert/supy-lcz-global/data/KL-KualaLumpurTest/output/grid/df_output_uMF_uLCu.h5 --dx 1000 --lat 3.056577 --lon 101.617373

python -m runner.runner KL-KualaLumpurTest5 --run-type grid --grid-size 1000 --grid-boxes 40 --metforc-src era5land --urbdesc-src lcz_updated --sitelist sitelist_custom --download-era5 -

python -m test_scripts.run_runner_test

python -m test_scripts.run_split_models

free -h --si (for WSL ram)

python -m runner.runner KL-KualaLumpur-2016_1month_s1 --run-type grid --grid-size 1000 --grid-boxes 5 --metforc-src era5land --urbdesc-src lcz_updated --sitelist KL-KualaLumpur-2016_splitlist --download-era5 --do-spinup


https://liveuclac.sharepoint.com/sites/Geography/ComputerSupport/
SSH Linux Geograhy Lab NW110A
ssh zcfaada@ad@durban.geog.ucl.ac.uk

Git repository
username: danish-abdulfata
PAT/password: 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
