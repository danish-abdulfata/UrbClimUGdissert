from __future__ import annotations

import os
os.environ['USE_PYGEOS'] = '0'

import argparse
from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path
from typing import Any
import georasters as gr
import numpy as np
import pandas as pd
import supy

from runner.utils import Buffer
from runner.utils import store_output_h5
from runner.utils import store_output_nc
from runner.utils import era5land_check_lsm
from runner.utils import gen_era5_forcing
from runner.utils import gen_era5land_forcing
from runner.utils import format_era5land_forcing
#from runner.utils import resample_forcing_data
from runner.utils import get_ee_data
from runner.utils import get_spinup_state
from runner.utils import check_lcz_for_zero
from runner.utils import get_city_from_site_list
from runner.utils import get_popdensity
from runner.utils import Grid
from runner.utils import update_supy_lcz_conversion_table


def _build_state_up(
        site_info: dict[str, Any],
        args: argparse.Namespace,
) -> pd.DataFrame:

    p_metainfo = Path(
        'data', site_info['sitename'], 'input', args.run_type,
        f"{site_info['sitename']}_sitedata_v1.csv",
    )
    df_meta = pd.read_csv(p_metainfo, index_col=[1])

    df_state_init, _ = supy.load_SampleData()

    # Use snow module, as discussed in Issue 96
    df_state_init.snowuse = 1

    # Issue with the settings for the porosity range of deciduous trees.
    # When porosity reaches 1 - the maximum value set in df_state -
    # all roughness-related calculations produce nan. Fix:
    df_state_init.pormin_dec = 0.1
    df_state_init.pormax_dec = 0.9

    df_state_baseline = df_state_init.copy()

    grid = df_state_baseline.index[0]
    df_state_baseline.loc[grid, "porosity_id"] = 0.5  # Issue 78

    df_meta_baseline = df_meta.loc[[
        'latitude',
        'longitude',
        'ground_height',
        'measurement_height_above_ground',
        'impervious_area_fraction',
        'tree_area_fraction',
        'grass_area_fraction',
        'bare_soil_area_fraction',
        'water_area_fraction',
    ]]
    # 0. physics options
    # 0.1 turn off snow module
    df_state_baseline.loc[grid, 'snowuse'] = 0
    # 0.2 use provided incoming longwave radiation
    df_state_baseline.loc[grid, 'netradiationmethod'] = 1

    # 1. coordinates
    df_state_baseline.loc[grid, ['lat', 'lng']] = df_meta_baseline.loc[
        ['latitude', 'longitude'], 'value'
    ].values

    # 2. altitude
    df_state_baseline.loc[grid, 'alt'] = df_meta_baseline.loc['ground_height', 'value']

    # 3. measurement height
    df_state_baseline.loc[grid, 'z'] = df_meta_baseline.loc[
        'measurement_height_above_ground', 'value'
    ]

    # 4. surface cover fractions
    df_state_baseline.loc[grid, 'sfr_surf'] = [
        # paved
        df_meta_baseline.loc['impervious_area_fraction', 'value'] * 0.7,
        # buildings
        df_meta_baseline.loc['impervious_area_fraction', 'value'] * 0.3,
        # evergreen trees
        df_meta_baseline.loc['tree_area_fraction', 'value'] / 2,
        # deciduous trees
        df_meta_baseline.loc['tree_area_fraction', 'value'] / 2,
        df_meta_baseline.loc['grass_area_fraction', 'value'],
        df_meta_baseline.loc['bare_soil_area_fraction', 'value'],
        df_meta_baseline.loc['water_area_fraction', 'value'],
    ]

    # 5. mean building height
    df_state_baseline.loc[grid, 'bldgh'] = 15.0
    #print('df_state_baseline',df_state_baseline.loc[grid, 'bldgh'])

    #supy.check_state(df_state_baseline)

    df_state_detailed = df_state_baseline.copy()
    grid = df_state_detailed.index[0]

    # 4. surface cover fractions
    df_state_detailed.loc[grid, 'sfr_surf'] = [
        df_meta.loc[['road_area_fraction', 'other_paved_area_fraction'], 'value'].sum(),
        df_meta.loc['roof_area_fraction', 'value'],
        # evergreen trees
        df_meta.loc['tree_area_fraction', 'value'] / 2,
        # deciduous trees
        df_meta.loc['tree_area_fraction', 'value'] / 2,
        df_meta.loc['grass_area_fraction', 'value'],
        df_meta.loc['bare_soil_area_fraction', 'value'],
        df_meta.loc['water_area_fraction', 'value'],
    ]

    # 5. mean building height
    df_state_detailed.loc[grid, 'bldgh'] = df_meta.loc['building_mean_height', 'value']
    #print('df_state_detailed',df_state_detailed.loc[grid, 'bldgh'])

    # 6. heights of roughness elements: building and tree
    #Vegetation heights not needed, as roughlnmommethod == 1??
    df_state_detailed.loc[grid, 'evetreeh'] = df_meta.loc['tree_mean_height', 'value']
    df_state_detailed.loc[grid, 'dectreeh'] = df_meta.loc['tree_mean_height', 'value']
    df_state_detailed.loc[grid, 'roughlenmommethod'] = 1
    df_state_detailed.loc[grid, 'z0m_in'] = df_meta.loc[
        'roughness_length_momentum', 'value'
    ]

    # 7. roughness length and zero-plane displacement
    df_state_detailed.loc[grid, 'zdm_in'] = df_meta.loc['displacement_height', 'value']

    # 8. population density
    df_state_detailed.loc[grid, ['popdensdaytime', 'popdensnighttime']] = (
        df_meta.loc['resident_population_density', 'value'] / 100
    )

    # 9. frontal area index (derived from `canyon_height_width_ratio`)
    # Actually, FAI is not used because we use roughlenmommethod == 1
    # Info: https://suews.readthedocs.io/en/latest/input_files/RunControl/scheme_options.html#cmdoption-arg-RoughLenMomMethod
    # df_state_detailed.loc[grid, ['faibldg', 'faidectree', 'faievetree']] = (
    #     df_meta.loc['canyon_height_width_ratio', 'value']
    #     * df_meta.loc['road_area_fraction', 'value']
    # )

    # 9. frontal area index (derived from Eq. 7 Lipson et al., ESSD, 2022)
    # In UP, tree fraction is evenly split between deciduous and evergreen
    # Thus the FAI is the same for both!
    faibldg = 2/np.pi * (1-df_meta.loc['roof_area_fraction', 'value']) * \
        df_meta.loc['canyon_height_width_ratio', 'value']
    df_state_detailed.loc[grid, 'faibldg'] = faibldg
    faitree = 2/np.pi * (1-df_meta.loc['tree_area_fraction', 'value']) * \
        df_meta.loc['canyon_height_width_ratio', 'value']
    df_state_detailed.loc[grid, ['faidectree', 'faievetree']] = faitree

    # 10. albedo
    df_state_detailed.loc[grid, 'alb'] = df_meta.loc['average_albedo_at_midday', 'value']
    df_state_detailed.loc[grid, 'albmax_dectr'] = df_meta.loc['average_albedo_at_midday', 'value']
    df_state_detailed.loc[grid, 'albmax_evetr'] = df_meta.loc['average_albedo_at_midday', 'value']
    df_state_detailed.loc[grid, 'albmax_grass'] = df_meta.loc['average_albedo_at_midday', 'value']
    df_state_detailed.loc[grid, 'albmin_dectr'] = df_meta.loc['average_albedo_at_midday', 'value']
    df_state_detailed.loc[grid, 'albmin_evetr'] = df_meta.loc['average_albedo_at_midday', 'value']
    df_state_detailed.loc[grid, 'albmin_grass'] = df_meta.loc['average_albedo_at_midday', 'value']
    df_state_detailed.loc[grid, 'albdectr_id'] = df_meta.loc['average_albedo_at_midday', 'value']
    df_state_detailed.loc[grid, 'albevetr_id'] = df_meta.loc['average_albedo_at_midday', 'value']
    df_state_detailed.loc[grid, 'albgrass_id'] = df_meta.loc['average_albedo_at_midday', 'value']


    if args.urbdesc_src == 'up_baseline':
        df_state_final = df_state_baseline
    elif args.urbdesc_src == 'up_detailed':
        df_state_final = df_state_detailed

    return df_state_final


def _suews_roi_from_pre_processor(
    roi: Grid | Buffer,
    lcz_rules: pd.DataFrame,
    lcz_raster: Path,
    output_path: Path,
) -> pd.DataFrame:

    # read in lcz raster and select first band
    grd_lcz = gr.from_file(lcz_raster.as_posix())

    # Clip from Buffer or Grid.
    # For buffer, select pixels that fall WITHIN circular buffer
    if isinstance(roi, Buffer):
        df_lcz_clip = grd_lcz.clip(roi.gdf, keep=True, all_touched=False)
        dct = {
            0: df_lcz_clip.iloc[0].GeoRaster.to_pandas().value_counts('value')
        }
    # For grid, select all pixels that touch the grid
    if isinstance(roi, Grid):
        df_lcz_clip = grd_lcz.clip(roi.gdf, keep=True, all_touched=True)
        dct = {
            roi: x.GeoRaster.to_pandas().value_counts('value')
            for roi, x in df_lcz_clip.iterrows()
        }
    # count LCZ categories
    df_lcz_count = pd.concat(dct, axis=1).T
    # we need to covert to int first, so the columns don't become `LZC1.0`
    df_lcz_count.columns = 'LCZ' + df_lcz_count.columns.astype(int).astype(str)
    df_lcz_count = df_lcz_count.reindex(lcz_rules.columns, axis=1)
    # Only keep the LCZ columns
    df_lcz_count = df_lcz_count.loc[:, df_lcz_count.columns.str.contains('LCZ') == True]
    # Set the pixel column as id
    df_lcz_count.index = df_lcz_count.index.rename('id')
    # calculate fractions of LCZ classes
    df_roi_lcz = df_lcz_count.apply(lambda ser: ser / ser.sum(), axis=1).replace(np.nan, 0)
    # the index for some reason becomes type object, store to file
    df_roi_lcz.index = pd.to_numeric(df_roi_lcz.index).astype(int)
    fn_df_roi_lcz = output_path / f'df_roi_lcz.csv'
    df_roi_lcz.to_csv(fn_df_roi_lcz)

    # convert LCZ to SUEWS using UMEP rules, save as file
    df_roi_suews = df_roi_lcz.dot(lcz_rules.T)
    fn_df_roi_suews = output_path / f'df_roi_suews.csv'
    df_roi_suews.to_csv(fn_df_roi_suews)

    return df_roi_suews


def _get_df_lcz_rules(
    roi: Buffer | Grid,
    site_info: dict[str, Any],
    args: argparse.Namespace,
    dx: float = 0.001,
) -> pd.DataFrame:

    xmin, ymin, xmax, ymax = roi.bounds
    info = {
        'xmin': xmin - dx,
        'xmax': xmax + dx,
        'ymin': ymin - dx,
        'ymax': ymax + dx,
        'odir': Path('data', site_info['sitename'], 'input', args.run_type),
    }
    # Read the SUPY-LCZ conversion table, as used in lcz_default
    df_lcz_rules = pd.read_csv('resources/lcz_to_suews_conversion.csv', index_col=0)

    # Both lcz_default and lcz_updated need the LCZ and POPDEN data
    # Only retrieve files when not available yet.
    fn_input = Path('data', site_info['sitename'], 'input', args.run_type)
    fn_lcz = sorted(fn_input.glob('*LCZ_Filter.tif'))
    if len(fn_lcz) > 0:
        print(" -----> LCZ data already on local drive")
    else:
        get_ee_data(info=info, data_source='LCZ')
        fn_lcz = sorted(fn_input.glob('*LCZ_Filter.tif'))

    # Check for zero's in LCZ, fill with neighbours if they exist
    check_lcz_for_zero(fn_lcz[0])

    fn_popden = sorted(fn_input.glob('*POPDEN.tif'))
    if len(fn_popden) > 0:
        print(" -----> POPDEN data already on local drive")
    else:
        get_ee_data(info=info, data_source='POPDEN')

    if args.urbdesc_src == 'lcz_updated':

        # Get the required OTHER data from EE
        fn_other = sorted(fn_input.glob('*LUC.tif')) + \
                   sorted(fn_input.glob('*GCFH.tif')) + \
                   sorted(fn_input.glob('*forest_type.tif'))
        if len(fn_other) >= 3:
            print(" -----> OTHER data already on local drive")
        else:
            get_ee_data(info=info, data_source='OTHER')

        # Update the SUPY-LCZ conversion table
        df_lcz_rules = update_supy_lcz_conversion_table(
            site_info=site_info,
            roi=roi,
            df_lcz_rule=df_lcz_rules,
            args=args,
        )

        # Add frontal area index (derived from Eq. 7 Lipson et al., ESSD, 2022)
        faibldg = 2 / np.pi * (1 - df_lcz_rules.loc['Buildings (-)']) * \
                  df_lcz_rules.loc['Height-to-width ratio (-)']
        df_lcz_rules.loc['Frontal area index buildings (-)'] = faibldg

        # For FAI trees, use H/W of LCZ A.
        fai_dectree = 2 / np.pi * (1 - df_lcz_rules.loc['Deciduous trees (-)']) * \
                  df_lcz_rules.loc['Height-to-width ratio (-)']
        df_lcz_rules.loc['Frontal area index deciduous tree (-)'] = fai_dectree
        fai_evetree = 2 / np.pi * (1 - df_lcz_rules.loc['Evergreen trees (-)']) * \
                  df_lcz_rules.loc['Height-to-width ratio (-)']
        df_lcz_rules.loc['Frontal area index evergeen tree (-)'] = fai_evetree

    # Store the table in output to keep track of this custom configuration
    output_path = Path('data', site_info['sitename'], 'output', args.run_type)
    output_path.mkdir(parents=True, exist_ok=True)

    sim_code = _get_simulation_code(args)
    output_file = output_path / f'LCZ-SUPY-CONVERSION_{sim_code}.csv'
    df_lcz_rules.to_csv(output_file)

    return df_lcz_rules


def _build_state_lcz(
        site_info: dict[str, Any],
        roi: Buffer | Grid,
        args: argparse.Namespace,
) -> pd.DataFrame:

    # First get the lcz-supy conversion table
    df_lcz_rules = _get_df_lcz_rules(
            roi=roi,
            site_info=site_info,
            args=args,
        )

    # Initialize the df_state
    # roughlenmommethod == 2 by default, deriving `z0m` and `zd`
    # from building and vegetation height
    df_state_init, _ = supy.load_SampleData()

    # Use snow module, as discussed in Issue 96
    df_state_init.snowuse = 1

    # Issue with the settings for the porosity range of deciduous trees.
    # When porosity reaches 1 - the maximum value set in df_state -
    # all roughness-related calculations produce nan. Fix:
    df_state_init.pormin_dec = 0.1
    df_state_init.pormax_dec = 0.9

    # Create the target Buffer or Grid?
    df_roi_suews = _suews_roi_from_pre_processor(
        roi=roi,
        lcz_rules=df_lcz_rules,
        lcz_raster=Path('data', site_info['sitename'],
                        'input', args.run_type, 'download.LCZ_Filter.tif'),
        output_path=Path('data', site_info['sitename'],
                         'output', args.run_type,)
    )
    # convert to supy format
    df_state = pd.concat([df_state_init] *
                         len(df_roi_suews), ignore_index=True)
    df_state.index = df_roi_suews.index.rename('grid')
    # assign LCZ info to supy `df_state`
    dict_rule_columns = {
        ('sfr_surf', '(0,)'): 'Paved (-)',
        ('sfr_surf', '(1,)'): 'Buildings (-)',
        ('sfr_surf', '(4,)'): 'Grass (-)',
        ('sfr_surf', '(3,)'): 'Deciduous trees (-)',
        ('sfr_surf', '(2,)'): 'Evergreen trees (-)',
        ('sfr_surf', '(5,)'): 'Bare soil (-)',
        ('sfr_surf', '(6,)'): 'Water (-)',
        ('bldgh', '0'): 'Mean building height (m)',
        ('evetreeh', '0'): 'Mean vegetation height (m)',
        ('dectreeh', '0'): 'Mean vegetation height (m)',
        ('faibldg', '0'): 'Frontal area index buildings (-)',
        ('faievetree', '0'): 'Frontal area index evergeen tree (-)',
        ('faidectree', '0'): 'Frontal area index deciduous tree (-)',
        ('alb', '(0,)'): 'Albedo (-)',
        ('alb', '(1,)'): 'Albedo (-)',
        ('alb', '(2,)'): 'Albedo (-)',
        ('alb', '(3,)'): 'Albedo (-)',
        ('alb', '(4,)'): 'Albedo (-)',
        ('alb', '(5,)'): 'Albedo (-)',
        ('alb', '(6,)'): 'Albedo (-)',
        ('albmax_dectr', '0'): 'Albedo (-)',
        ('albmax_evetr', '0'): 'Albedo (-)',
        ('albmax_grass', '0'): 'Albedo (-)',
        ('albmin_dectr', '0'): 'Albedo (-)',
        ('albmin_evetr', '0'): 'Albedo (-)',
        ('albmin_grass', '0'): 'Albedo (-)',
        ('albdectr_id', '0'): 'Albedo (-)',
        ('albevetr_id', '0'): 'Albedo (-)',
        ('albgrass_id', '0'): 'Albedo (-)',
    }
    df_state.loc[:, dict_rule_columns.keys()] = \
        df_roi_suews.loc[:, dict_rule_columns.values()].values

    # Change the population density, for both LCZ default and updated
    # [OLD] Pop density from GWP_v4, divide by 100 for people/ha
    # [OLD] Pop density from GHSL-2019, divide by 6.25 for people/ha
    # [CURRENT] Pop density from GHSL-2022, already in # people / ha
    gee_popden = get_popdensity(site_info, roi, args)
    df_state.popdensdaytime = gee_popden
    df_state.popdensnighttime = gee_popden
    df_state.porosity_id = 0.5  # Issue 78

    return df_state

def _build_forcing_up(
        site_info: pd.Series,
        args: argparse.Namespace,
) -> pd.DataFrame:

    input_dir = Path('data', site_info['sitename'], 'input')


    print(f' -----> Getting UP data as metforcing')
    forcings = sorted(input_dir.glob(
        f'{site_info["sitename"].replace("-debug","")}_*_data.txt'
    ))

    # Limited influence of new resampling, stick to the default
    # df_forcing_raw = pd.concat(
    #     [supy.util.read_forcing(
    #         f,
    #         tstep_mod=None,
    #     ) for f in forcings]
    # )
    #
    # # Do resampling to 300s (SUEWS's default
    # # Different from default workflow in SUPY
    # print(f' -----> Resampling UP data to model timestep')
    # df_forcing = resample_forcing_data(
    #     data_met_raw=df_forcing_raw,
    #     tstep_in=site_info['timestep_interval_seconds'],
    #     tstep_mod=300,
    # )

    # Use default resampling of input data
    df_forcing = pd.concat(
        [supy.util.read_forcing(
            f,
            tstep_mod=300,
        ) for f in forcings]
    )

    # Times in UTC
    start = site_info['time_coverage_start']
    start_analysis = site_info['time_analysis_start']
    end = site_info['time_coverage_end']

    # Offset from UTC to Local
    utc_offset = int(site_info['local_utc_offset_hours'])

    # Times in Local Time
    start_lt = pd.to_datetime(start) + timedelta(hours=utc_offset)
    start_analysis_lt = pd.to_datetime(start_analysis) + timedelta(hours=utc_offset)
    end_lt = pd.to_datetime(end) + timedelta(hours=utc_offset)

    # Provided Observed UP forcing is in Local Time - from Ting
    df_forcing = df_forcing.loc[start_lt:end_lt]

    print("     |-> checking the UP metforcing ...")
    # https://github.com/UMEP-dev/SuPy/blob/8319c9063c0b030608f9ad11c591306ce8814f70/src/supy/_check.py
    df_forcing = supy.check_forcing(df_forcing, fix=True)

    # Overwrite analysis period forcing with ERA5 forcing
    if 'era5' in args.metforc_src:

        if args.metforc_src == 'era5':

            print(f' -----> Using raw ERA5 data as metforcing for analysis period')
            # Data needs to be downloaded from CDS, and converted to supy format
            # See: https://github.com/UMEP-dev/SuPy/blob/00f7073d796cf21d1fa0a8684837f03088437d09/src/supy/util/_era5.py#L670-L673
            dir_save = Path('data', site_info['sitename'], 'input', 'era5')
            dir_save.mkdir(parents=True, exist_ok=True)

            #TODO: check how to treat this within the runner context - very slow
            if args.download_era5:
                print("     |-> Downloading ERA5 forcing. This may take some time ...")
                gen_era5_forcing(
                    args=args,
                    site_info=site_info,
                    dir_save=dir_save,
                    spinup_days=0,
                )
            else:
                print("     |-> Downloading ERA5 forcing skipped.")

            # era5 forcing files
            era5_forcings = sorted(dir_save.glob('ERA5_*_data_60.txt'))


        if args.metforc_src == 'era5land':

            print(f' -----> Using raw ERA5Land data as metforcing for analysis period')
            # Data needs to be downloaded from CDS, and converted to supy format
            # See: https://github.com/UMEP-dev/SuPy/blob/00f7073d796cf21d1fa0a8684837f03088437d09/src/supy/util/_era5.py#L670-L673
            dir_save = Path('data', site_info['sitename'], 'input', 'era5land')
            dir_save.mkdir(parents=True, exist_ok=True)

            # Check validity of pixels on dedicated coordinates.
            # If land fraction < 0.5, pixel has no data. In that case,
            # a neighbouring pixel is taken automatically.
            new_lon_lsm, new_lat_lsm = era5land_check_lsm(site_info, dir_save)

            if args.download_era5:
                print("     |-> Downloading ERA5-LAND forcing. This may take some time ...")
                gen_era5land_forcing(
                    args=args,
                    longitude=new_lon_lsm,
                    latitude=new_lat_lsm,
                    site_info=site_info,
                    dir_save=dir_save,
                    spinup_days=0,
                )
            else:
                print("     |-> Downloading ERA5-LAND forcing skipped.")

            print(" -----> Make the ERA5-LAND forcing readable by SUPY")
            # This routine also retrieves the local z0m value,
            # based on ERA5Land vegetation characteristics
            format_era5land_forcing(
                lon=new_lon_lsm,
                lat=new_lat_lsm,
                dir_save=dir_save,
                hgt_agl_diag=100)

            # era5-land forcing files
            era5_forcings = sorted(dir_save.glob('ERA5LAND_UTC_*_data_60.txt'))

        # Limited influence of new resampling, stick to the default
        # df_era5_forcing_raw = pd.concat(
        #     [supy.util.read_forcing(
        #         f,
        #         tstep_mod=None,
        #     ) for f in era5_forcings]
        # )
        #
        # # Do resampling to 300s (SUEWS's default
        # # Different from default workflow in SUPY
        # print(f' -----> Resampling ERA5 data to model timestep')
        # df_era5_forcing = resample_forcing_data(
        #     data_met_raw=df_era5_forcing_raw,
        #     tstep_in=3600,
        #     tstep_mod=300,
        # )

        # Use default resampling of input data
        df_era5_forcing = pd.concat(
            [supy.util.read_forcing(
                f,
                tstep_mod=300,
            ) for f in era5_forcings]
        )

        # change ERA forcing to Local time, as UP forcing is in LT (needed by SUPY)
        df_era5_forcing.index = df_era5_forcing.index + timedelta(hours=utc_offset)
        df_era5_forcing['iy'] = df_era5_forcing.index.year
        df_era5_forcing['id'] = df_era5_forcing.index.dayofyear
        df_era5_forcing['it'] = df_era5_forcing.index.hour
        df_era5_forcing['imin'] = df_era5_forcing.index.minute
        df_era5_forcing['isec'] = df_era5_forcing.index.second

        print(" -----> checking the ERA forcing ...")
        # https://github.com/UMEP-dev/SuPy/blob/8319c9063c0b030608f9ad11c591306ce8814f70/src/supy/_check.py
        df_era5_forcing = supy.check_forcing(df_era5_forcing, fix=True)

        # Overwrite UP analysis forcing with ERA-5 forcing, in Local Time
        df_forcing.loc[start_analysis_lt:end_lt] = df_era5_forcing.loc[start_analysis_lt:end_lt]

        # Check the final forcing again
        print(" -----> checking again with the merged UP+ERA5 forcing ...")
        # https://supy.readthedocs.io/en/latest/tutorial/setup-own-site.html#load-and-resample-forcing-data
        df_forcing = supy.check_forcing(df_forcing, fix=True)

    # pressure must be in kPa, do AFTER check_forcing only!
    # NOT needed, as run_supy needs pressure in hpa
    # df_forcing['pres'] = df_forcing['pres'] / 10

    print(" -----> save the final forcing to file ...")
    output_dir = Path('data', site_info['sitename'], 'output', args.run_type)
    sim_code = _get_simulation_code(args)
    final_forcing_file = output_dir / f'df_final_forcing_{sim_code}.h5'

    df_forcing.to_hdf(
        final_forcing_file,
        key="df_forcing",
        complevel=9,
        complib="blosc:lz4hc",
    )
    print(f' -----> Final forcing saved to {final_forcing_file}')

    return df_forcing


def _build_forcing(
        site_info: pd.Series,
        args: argparse.Namespace,
        spinup_days: int,
) -> pd.DataFrame:

    # Times in UTC
    start_analysis = site_info['time_analysis_start']
    start = pd.to_datetime(start_analysis) - timedelta(days=spinup_days)
    end = site_info['time_coverage_end']

    # Offset from UTC to Local
    utc_offset = int(site_info['local_utc_offset_hours'])

    # Times in Local Time
    start_lt = pd.to_datetime(start) + timedelta(hours=utc_offset)
    start_analysis_lt = pd.to_datetime(start_analysis) + timedelta(hours=utc_offset)
    end_lt = pd.to_datetime(end) + timedelta(hours=utc_offset)

    # Overwrite analysis period forcing with ERA5 forcing
    if 'era5' in args.metforc_src:

        # TODO: Not used, can be removed from Tool code?
        if args.metforc_src == 'era5':

            print(f' -----> Using raw ERA5 data as metforcing for analysis period')
            # Data needs to be downloaded from CDS, and converted to supy format
            # See: https://github.com/UMEP-dev/SuPy/blob/00f7073d796cf21d1fa0a8684837f03088437d09/src/supy/util/_era5.py#L670-L673
            dir_save = Path('data', site_info['sitename'], 'input', 'era5')
            dir_save.mkdir(parents=True, exist_ok=True)

            #Downloading from CDS is very slow, therefor moved to ERA5Land
            if args.download_era5:
                print("     |-> Downloading ERA5 forcing. This may take some time ...")
                gen_era5_forcing(
                    args= args,
                    site_info= site_info,
                    dir_save=dir_save,
                    spinup_days=spinup_days,
                )
            else:
                print("     |-> Downloading ERA5 forcing skipped.")

            # era5 forcing files
            era5_forcings = sorted(dir_save.glob('ERA5_*_data_60.txt'))


        if args.metforc_src == 'era5land':

            print(f' -----> Using raw ERA5Land data as metforcing for analysis period')
            # Data needs to be downloaded from CDS, and converted to supy format
            # See: https://github.com/UMEP-dev/SuPy/blob/00f7073d796cf21d1fa0a8684837f03088437d09/src/supy/util/_era5.py#L670-L673
            dir_save = Path('data', site_info['sitename'], 'input', 'era5land')
            dir_save.mkdir(parents=True, exist_ok=True)

            # Check validity of pixels on dedicated coordinates.
            # If land fraction < 0.5, pixel has no data. In that case,
            # a neighbouring pixel is taken automatically.
            new_lon_lsm, new_lat_lsm = era5land_check_lsm(site_info, dir_save)

            # Extract ERA5Land data from GEE, with ot without spin-up days
            if args.download_era5:
                print("     |-> Downloading ERA5-LAND forcing. This may take some time ...")
                gen_era5land_forcing(
                    args=args,
                    longitude=new_lon_lsm,
                    latitude=new_lat_lsm,
                    site_info=site_info,
                    dir_save=dir_save,
                    spinup_days=spinup_days,
                )
            else:
                print("     |-> Downloading ERA5-LAND forcing skipped.")

            print(" -----> Make the ERA5-LAND forcing readable by SUPY")
            # This routine also retrieves the local z0m value,
            # based on ERA5Land vegetation characteristics
            format_era5land_forcing(
                lon=new_lon_lsm,
                lat=new_lat_lsm,
                dir_save=dir_save,
                hgt_agl_diag=100)

            # era5-land forcing files
            era5_forcings = sorted(dir_save.glob('ERA5LAND_UTC_*_data_60.txt'))

        # Limited influence of new resampling, stick to the default
        # df_era5_forcing_raw = pd.concat(
        #     [supy.util.read_forcing(
        #         f,
        #         tstep_mod=None,
        #     ) for f in era5_forcings]
        # )
        #
        # # Do resampling to 300s (SUEWS's default
        # # Different from default workflow in SUPY
        # print(f' -----> Resampling ERA5 data to model timestep')
        # df_era5_forcing = resample_forcing_data(
        #     data_met_raw=df_era5_forcing_raw,
        #     tstep_in=3600,
        #     tstep_mod=300,
        # )

        # Use default resampling of input data
        df_era5_forcing = pd.concat(
            [supy.util.read_forcing(
                f,
                tstep_mod=300,
            ) for f in era5_forcings]
        )

        # change ERA forcing to Local time, required by SUEWS
        df_era5_forcing.index = df_era5_forcing.index + timedelta(hours=utc_offset)
        df_era5_forcing['iy'] = df_era5_forcing.index.year
        df_era5_forcing['id'] = df_era5_forcing.index.dayofyear
        df_era5_forcing['it'] = df_era5_forcing.index.hour
        df_era5_forcing['imin'] = df_era5_forcing.index.minute
        df_era5_forcing['isec'] = df_era5_forcing.index.second

        # Return final forcing, with or without two spin-up years
        if args.do_spinup:
            df_forcing = df_era5_forcing.loc[start_lt:end_lt].copy()
        else:
            df_forcing = df_era5_forcing.loc[start_analysis_lt:end_lt].copy()

        print(" -----> checking the ERA5 forcing ...")
        # https://github.com/UMEP-dev/SuPy/blob/8319c9063c0b030608f9ad11c591306ce8814f70/src/supy/_check.py
        df_forcing = supy.check_forcing(df_forcing, fix=True)

    # pressure must be in kPa, do AFTER check_forcing only!
    # NOT needed, as run_supy needs pressure in hpa
    # df_forcing['pres'] = df_forcing['pres'] / 10

    print(" -----> save the final forcing to file ...")
    output_dir = Path('data', site_info['sitename'], 'output', args.run_type)
    sim_code = _get_simulation_code(args)
    final_forcing_file = output_dir / f'df_final_forcing_{sim_code}.h5'

    df_forcing.to_hdf(
        final_forcing_file,
        key="df_forcing",
        complevel=9,
        complib="blosc:lz4hc",
    )
    print(f' -----> Final forcing saved to {final_forcing_file}')

    return df_forcing


def _get_simulation_code(args: argparse.Namespace) -> str:

    # For the Urban Description (UD)
    if args.urbdesc_src == 'up_baseline':
        ud_value = 'sLC'
    elif args.urbdesc_src == 'up_detailed':
        ud_value = 'sLC'
    elif args.urbdesc_src == 'lcz_default':
        # Default conversion table
        ud_value = 'uLCd'
    elif args.urbdesc_src == 'lcz_updated':
        # Updated conversion table - not necessarily better
        ud_value = 'uLCu'

    # for the Meteorological Forcing:
    if args.metforc_src == 'obs':
        # Forcing as provided by UP, based on flux tower observations
        mf_value = 'sMF'
    elif args.metforc_src == 'era5':
        # Raw ERA5 forcing
        mf_value = 'uMF'
    elif args.metforc_src == 'era5land':
        # Raw ERA5 Land forcing from Google Earth Engine
        mf_value = 'uMF'

    sim_code = f'{mf_value}_{ud_value}'

    return sim_code


def main(argv: Sequence[str] | None = None) -> int:

    # Read the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('city', nargs='*')
    parser.add_argument('--run-type', choices=('buffer', 'grid'))
    parser.add_argument('--grid-size', type=float, default=1000)
    parser.add_argument('--grid-boxes', type=int, default=13)
    parser.add_argument('--metforc-src',
                        choices=('obs', 'era5', 'era5land'), default='obs')
    parser.add_argument('--urbdesc-src',
                        choices=('up_baseline', 'up_detailed',
                                 'lcz_default', 'lcz_updated'), default='up_detailed')
    # parser.add_argument('--metforc-src',
    #                     choices=('obs', 'era5land'),
    #                     default='obs')
    # parser.add_argument('--urbdesc-src',
    #                     choices=('up_detailed','lcz_updated'),
    #                     default='up_detailed')
    parser.add_argument('--download-era5', action='store_true') # default is false
    parser.add_argument('--initialize-only', action='store_true') # default is false
    parser.add_argument('--do-spinup', action='store_true')  # default is false
    parser.add_argument('--use-rdp', action='store_true')  # default is false
    parser.add_argument(
        '--sitelist',
        type=str,
        help='File with custom site list information (without file extension)',
    )

    args = parser.parse_args(argv)

    # some cities have spaces in them :(
    args.city = ' '.join(args.city)
    site_info = get_city_from_site_list(args)

    print(f"==> running for sitename {site_info['sitename']}")

    # Get the provided footprint of the flux tower
    if site_info['surface_cover_radius'] == 'fpm':
        # use 500 m as default if there is no info provided
        buffer_size = 500
    else:
        buffer_size = int(site_info['surface_cover_radius'])

    # Create in- and output paths
    input_path = Path('data', site_info['sitename'], 'input', args.run_type)
    input_path.mkdir(parents=True, exist_ok=True)
    output_path = Path('data', site_info['sitename'], 'output', args.run_type)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create the requested ROI, either Buffer around point or Grid
    print(f'==> running using run_type {args.run_type!r}')
    if args.run_type == 'buffer':
        roi: Buffer | Grid = Buffer.from_point(
            lon=site_info['longitude'],
            lat=site_info['latitude'],
            # use the given buffer if in buffer mode
            buffer_rad=buffer_size,
        )
    else:
        roi = Grid.from_point(
            lon=site_info['longitude'],
            lat=site_info['latitude'],
            nx=args.grid_boxes,
            dx=args.grid_size,
        )
        # Store grid to file
        roi_ofile = Path('data', site_info['sitename'], 'input', args.run_type, "roi_grid.shp")
        roi.to_file(roi_ofile)

    # Build state, from UP obs or LCZ
    print(f'==> building state, based on {args.urbdesc_src}')
    if 'up_' in args.urbdesc_src:
        df_state = _build_state_up(
            site_info=site_info,
            args=args
        )
    elif 'lcz_' in args.urbdesc_src:
        df_state = _build_state_lcz(
        site_info=site_info,
        roi=roi,
        args=args
        )

    # Check the state
    supy.check_state(df_state)

    # Store the df_state in the relevant output folder, to keep track of settings
    sim_code = _get_simulation_code(args)
    state_file = output_path / f'df_state_{sim_code}.pkl'
    df_state.to_pickle(state_file)

    # Use prepared state in case of RDP LC information
    # Pre-process the file with helper_scripts/create_state_rdp.py
    if args.use_rdp:
        fn_state_rdp = output_path / f'df_state_{sim_code}_rdp.pkl'
        df_state = pd.read_pickle(fn_state_rdp)

    # Build the meteoforcing, from UP obs and / or ERA5
    # Set spin-up length (in days)
    spinup_days = 10

    # Takes a bit of time, skip when interested in initializing df_state only
    # Options for the buffer case
    print(f'==> building meteorological forcing: {args.metforc_src}')
    if args.run_type == 'buffer':
        # Unknown site, no forcing available
        # All data (including spin-up) will thus come from ERA5-Land
        if args.sitelist is not None:
            df_forcing = _build_forcing(
                site_info=site_info,
                args=args,
                spinup_days=spinup_days,
            )
        # UP site, for which spin-up is available
        else:
            df_forcing = _build_forcing_up(
                site_info=site_info,
                args=args
            )

    # For the grid simulations, no forcing data is available.
    # All data (including spin-up) will thus come from ERA5-Land
    elif args.run_type == 'grid':
        df_forcing = _build_forcing(
            site_info=site_info,
            args=args,
            spinup_days=spinup_days,
        )

    # Check if spin-up is required for final **universal** simulation
    if (args.sitelist is not None):

        # Times in UTC
        start_analysis = site_info['time_analysis_start']
        start = pd.to_datetime(start_analysis) - timedelta(days=spinup_days)
        end = site_info['time_coverage_end']

        # Offset from UTC to Local
        utc_offset = int(site_info['local_utc_offset_hours'])

        # Times in Local Time
        start_lt = pd.to_datetime(start) + timedelta(hours=utc_offset)
        start_analysis_lt = pd.to_datetime(start_analysis) + timedelta(hours=utc_offset)
        end_lt = pd.to_datetime(end) + timedelta(hours=utc_offset)

        if (args.do_spinup):

            if args.run_type == 'grid':
                # Create a spin-up state for the whole grid
                print(f'==> Spinning up the states of all surface fractions')
                df_state = get_spinup_state(
                    site_info=site_info,
                    df_state=df_state,
                    df_forcing=df_forcing,
                    spinup_days=spinup_days
                )
                # Validate the state again
                supy.check_state(df_state)
                # Reduce forcing to analysis time
                df_forcing = df_forcing.loc[start_analysis_lt:end_lt]

            elif args.run_type == 'buffer':
                print(f'==> Include spin-up time for this buffer run')
                df_forcing = df_forcing.loc[start_lt:end_lt]

        else:
            df_forcing = df_forcing.loc[start_analysis_lt:end_lt]
    # Launch the simulation
    if args.initialize_only:
        print(f'==> Initialization only, supy not run!')
        #print(df_forcing)
        #print(df_state)

    else:
        print(f'==> start the simulation')
        df_output, df_state_final = supy.run_supy(
            df_forcing=df_forcing,
            df_state_init=df_state,
        )

        print(f'==> simulation completed!')
        print(f'==> storing the outputs now ...')

        # Store final state
        final_state_file = output_path / f'df_state_final_{sim_code}.pkl'
        df_state_final.to_pickle(final_state_file)

        # Store raw output - VERY LARGE FILE.
        if 'debug' in args.city:
            df_output_raw_file = output_path / f'df_output_raw_{sim_code}.h5'
            df_output.to_hdf(
                df_output_raw_file,
                key=f"df_output",
                complevel=9,
                complib="blosc:lz4hc",
            )

        # Store SUEWS variables, on timestep_interval, only for time_analysis_start (h5)
        # for the universal tool, output should be hourly!
        if (args.sitelist is not None):
            freq_out = int(60)
        else:
            freq_out = int(site_info['timestep_interval_seconds'] / 60)
        suews_output_file = output_path / f'df_output_{sim_code}.h5'
        store_output_h5(df_output, site_info, suews_output_file, freq_out)
        print(f'==> output stored as as .h5 file')

        # Store same output also in Urban-Plumber format (netcdf)
        if args.run_type == 'buffer':
            suews_output_file_up = output_path / f'output_{sim_code}.nc'
            store_output_nc(args, site_info, sim_code, suews_output_file_up)
            print(f'==> output converted to Urban Plumber format')

    print(f'==> all output is available in {output_path}/')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
