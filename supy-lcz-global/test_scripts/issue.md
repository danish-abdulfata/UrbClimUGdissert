
Wrong coordinates for structure_grid_output.py nc file	

@sunt05 @chrisbrierley I managed to successfully run the SuPy_LCZ model for CH-Shanghai (Grid) case without any hiccups. 

I have checked the output folder in `.\data\CH-Shanghai\output\grid` ([found here](https://liveuclac-my.sharepoint.com/:f:/g/personal/zcfaada_ucl_ac_uk/EgfCEYzv_HtDmwneLWT5t6sBJBfl3OYboQFHB21PPe61Aw?e=8NtoQF)) to see if the data is reasonable/correct.

However, the issue comes with running `helpful_scripts\structure_grid_output.py`. The output `.nc` file it produces has the wrong coordinates when mapped in qGIS (the file is also in `.\output\grid`). 

It should be noted however that I failed to run `structure_grid_output.py` until I wiped and reinstalled the `supy_lcz` environment. 

### Steps for the issue:

1. I ran SuPy under the suggested `quickstart.md` prompt: `python -m runner.runner CH-Shanghai --run-type grid --grid-size 300 --grid-boxes 3 --metforc-src era5land --urbdesc-src lcz_updated --sitelist sitelist_custom --download-era5` under the micromamba supy_lcz environment as noted in `fixed_env.yml`.

2. Output `.h5` files were created in `.\data\CH-Shanghai\output\grid\`.

3. I made a copy of `.\helpful_scripts\structure_grid_output.py` in `.\test_scripts\`.

		- I was testing different arguments for the script, but in the end, stuck with the original (ie. script is unchanged, just in a different folder). 
		
4.  I ran `python -m test_scripts.structure_grid_output.py --dx --lat --long` (FILL CORRECT COMMAND) in the terminal.

5.  Output `.nc` files were created in `.\data\CH-Shanghai\output\grid`.

6.  I loaded and compared `CH-Shanghai\input\grid\roi_grid.shp` to `df_output_uMF_uLCu_latlon.nc` and `df_output_uMF_uLCu.nc` with the 'ESG 4629' (Check if correct) projection.

7.  The convered `.h5` files have coordinates totally wrong from the original site, located in the pacific rather than central China. See attached image below. 

Example image:
World Map layer generated from qGIS defaults. 

*Thoughts*

I was double checking the reprojection algorithm used to see if the calculations were any different from `runner.py` and `utils.py`, but everything seemed correct. I tweaked around with the arguments and re-enabled `--nx` if it would help but it did not. Grid size and number of grids are correct. The issue is only to do with the coordinate mismatch for the created `.nc` files.

I was thinking it could possibly be from different definitions for using the lat/long coordinates within the 2 scripts (ie. centre of the grid versus the corner of the grid), but even if, the discrepancy shouldn't be as large as it is. 