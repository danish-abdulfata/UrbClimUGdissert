
Fortran error running my own script `run_split_models.py`

'''
(supy_lcz) danish@Danish-DESKTOP:/mnt/c/Users/Danish/Documents/GitHub/UrbClimUGdissert/supy-lcz-global$ python -m test_scripts.run_split_models
*** Earth Engine *** Share your feedback by taking our Annual Developer Satisfaction Survey: https://google.qualtrics.com/jfe/form/SV_0JLhFqfSY1uiEaW?source=Init
Split factor of 3 is valid. Site will be split into 64 runs at 25.0 grids per run
--------> KL-KualaLumpur-2016_1month_custom.csv successfully created. Starting SuPy models...
==> running for sitename KL-KualaLumpur-2016_1month_s1
==> running using run_type 'grid'
==> building state, based on lcz_updated
/home/danish/micromamba/envs/supy_lcz/lib/python3.12/site-packages/ee/deprecation.py:207: DeprecationWarning:

Attention required for RUB/RUBCLIM/LCZ/global_lcz_map/v1! You are using a deprecated asset.
To ensure continued functionality, please update it.
Learn more: https://developers.google.com/earth-engine/datasets/catalog/RUB_RUBCLIM_LCZ_global_lcz_map_v1

  warnings.warn(warning, category=DeprecationWarning)
 -----> Downloading LCZ data from Google's Earth Engine ...
     |-> LCZ downloaded from GEE and extracted in: data/KL-KualaLumpur-2016_1month_s1/input/grid
     |-> No LCZ pixels with 0's
 -----> Downloading POPDEN data from Google's Earth Engine ...
     |-> POPDEN downloaded from GEE and extracted in: data/KL-KualaLumpur-2016_1month_s1/input/grid
Exporting OTHER data to Google Drive
 -----> Downloading OTHER data from Google's Earth Engine ...
     |-> OTHER downloaded from GEE and extracted in: data/KL-KualaLumpur-2016_1month_s1/input/grid
 -----> Updating the lcz_to_suews_conversion table ...
     |-> Fractions sum to 1 for LCZ 3
     |-> No tree type data available for LCZ 3
     |-> Average tree height added for LCZ 3
     |-> Fractions sum to 1 for LCZ 6
     |-> Fractions sum to 1 after assigning tree types for LCZ 6
     |-> Average tree height added for LCZ 6
     |-> Fractions sum to 1 for LCZ 8
     |-> Fractions sum to 1 after assigning tree types for LCZ 8
     |-> Average tree height added for LCZ 8
     |-> Fractions sum to 1 for LCZ 9
     |-> Fractions sum to 1 after assigning tree types for LCZ 9
     |-> Average tree height added for LCZ 9
     |-> Fractions sum to 1 for LCZ 11
     |-> Fractions sum to 1 after assigning tree types for LCZ 11
     |-> Average tree height added for LCZ 11
     |-> Fractions sum to 1 for LCZ 12
     |-> Fractions sum to 1 after assigning tree types for LCZ 12
     |-> Average tree height added for LCZ 12
     |-> Fractions sum to 1 for LCZ 14
     |-> No tree type data available for LCZ 14
     |-> Average tree height added for LCZ 14
2024-11-21 21:42:36,983 - SuPy - INFO - All cache cleared.
2024-11-21 21:42:38,853 - SuPy - INFO - SuPy is validating `df_state`...
2024-11-21 21:42:39,802 - SuPy - INFO - All checks for `df_state` passed!
==> building meteorological forcing: era5land
 -----> Using raw ERA5Land data as metforcing for analysis period
     |-> Selected pixel is valid.
     |-> Downloading ERA5-LAND forcing. This may take some time ...
    -- Retrieving: 2015-12-20 - 2016-01-13
 -----> Make the ERA5-LAND forcing readable by SUPY
 -----> checking the ERA5 forcing ...
2024-11-21 21:42:42,453 - SuPy - INFO - SuPy is validating `df_forcing`...
2024-11-21 21:42:42,458 - SuPy - INFO - All checks for `df_forcing` passed!
 -----> save the final forcing to file ...
 -----> Final forcing saved to data/KL-KualaLumpur-2016_1month_s1/output/grid/df_final_forcing_uMF_uLCu.h5
==> Spinning up the states of all surface fractions
2024-11-21 21:42:42,620 - SuPy - INFO - ====================
2024-11-21 21:42:42,620 - SuPy - INFO - Simulation period:
2024-11-21 21:42:42,620 - SuPy - INFO -   Start: 2015-12-22 08:00:00
2024-11-21 21:42:42,620 - SuPy - INFO -   End: 2016-01-01 08:00:00
2024-11-21 21:42:42,621 - SuPy - INFO -
2024-11-21 21:42:42,622 - SuPy - INFO - No. of grids: 7
2024-11-21 21:42:42,622 - SuPy - INFO - SuPy is running in parallel mode
At line 1233 of file /project/src/suews/src/suews_phys_rslprof.f95
Fortran runtime error: Index '0' of dimension 1 of array 'z' below lower bound of 1
'''

Running a more basic version of the script `test_scripts/run_runner_test.py` works as intended. 

I am not sure what is causing SuPy to run at the wrong grid size.