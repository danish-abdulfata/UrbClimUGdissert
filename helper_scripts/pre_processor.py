from __future__ import annotations

import os
import traceback
import zipfile as zp
from pathlib import Path
from typing import Any
from typing import Hashable
from typing import Iterator
from typing import Literal

import ee
import geopandas as gpd
import georasters as gr
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from pyproj import CRS
from pyproj import Transformer
from requests import get
from shapely.geometry import Point
from shapely.geometry import Polygon
import rioxarray as rxr
import xarray as xr
import supy
from datetime import timedelta

ee.Initialize()

def _get_roi_geometry(info: dict[str, Any]) -> ee.Geometry:

    roi = ee.Geometry.Polygon(
        [[[info['xmin'], info['ymin']],
          [info['xmax'], info['ymin']],
          [info['xmax'], info['ymax']],
          [info['xmin'], info['ymax']]]],
        None, False)
    return roi
def get_ee_data(
    info: dict[str, Any],
    data_source: Literal['LCZ', 'POPDEN', 'OTHER'],
) -> None:

    # Get region of interest
    roi = _get_roi_geometry(info).bounds()

    print("Preparing the data on Google's Earth Engine")
    if data_source == 'LCZ':

        # LCZ map, from Demuzere et al. (2022)
        # After mosaicing, projection info is lost, so add back
        lcz_proj = ee.ImageCollection("RUB/RUBCLIM/LCZ/global_lcz_map/v1").first() \
            .projection()
        img = ee.ImageCollection("RUB/RUBCLIM/LCZ/global_lcz_map/v1") \
            .mosaic() \
            .select("LCZ_Filter") \
            .setDefaultProjection(lcz_proj) \
            .clip(roi)

        bands = img.bandNames().getInfo()

        # Create download path
        url = img.getDownloadUrl({'bands': bands, 'region': roi})

        # Create path to store img .zip file
        img_path = info['odir'] / "LCZ_Filter_map.zip"

    elif data_source == 'POPDEN':

        # Get population density, from 2020 (# people / km2).
        # Data: https://developers.google.com/earth-engine/datasets/catalog/CIESIN_GPWv411_GPW_UNWPP-Adjusted_Population_Density
        popden = ee.ImageCollection("CIESIN/GPWv411/GPW_UNWPP-Adjusted_Population_Density") \
            .filterDate('2020-01-01', '2021-01-01') \
            .first() \
            .select('unwpp-adjusted_population_density') \
            .rename('POPDEN')

        img = popden \
            .toInt()

        bands = img.bandNames().getInfo()

        # Create download path
        url = img.getDownloadUrl({'bands': bands, 'region': roi})

        # Create path to store img .zip file
        img_path = info['odir'] / "popden_map.zip"

    elif data_source == 'OTHER':

        # # Define the available ahf products
        # ahf_products = {
        #     'dong17': 'Dong_etal_2017/ahe_v2me_anl_f',
        #     'varquez21': 'Varquez_etal_2021/AHE_2010_year_fix',
        #     'jin19': 'Jin_etal/global_AHF2015',
        #     'flanner09': 'Flanner2009/AHF_2005_2_5min',
        # }
        #
        # if ahf_monthly:
        #     ahf_source = "varquez21"
        #     print("Montly AHF values requested, using the 'varquez21' data by default.")
        # else:
        #     ahf_source = ahf_source
        #
        # allowed_ahf = ['dong17', 'varquez21', 'jin19', 'flanner09']
        # if ahf_source not in allowed_ahf:
        #     print(
        #         f"You need to provide one of the following ahf sources: "
        #         f"{', '.join(allowed_ahf)}"
        #     )
        #
        # ee_ahf_src = "projects/WUDAPT/AHF"
        # if ahf_monthly:
        #     ahf01 = ee.Image(f"{ee_ahf_src}/Varquez_etal_2021/AHE_2010_01_average_fix").rename("AHF_01")
        #     ahf02 = ee.Image(f"{ee_ahf_src}/Varquez_etal_2021/AHE_2010_02_average_fix").rename("AHF_02")
        #     ahf03 = ee.Image(f"{ee_ahf_src}/Varquez_etal_2021/AHE_2010_03_average_fix").rename("AHF_03")
        #     ahf04 = ee.Image(f"{ee_ahf_src}/Varquez_etal_2021/AHE_2010_04_average_fix").rename("AHF_04")
        #     ahf05 = ee.Image(f"{ee_ahf_src}/Varquez_etal_2021/AHE_2010_05_average_fix").rename("AHF_05")
        #     ahf06 = ee.Image(f"{ee_ahf_src}/Varquez_etal_2021/AHE_2010_06_average_fix").rename("AHF_06")
        #     ahf07 = ee.Image(f"{ee_ahf_src}/Varquez_etal_2021/AHE_2010_07_average_fix").rename("AHF_07")
        #     ahf08 = ee.Image(f"{ee_ahf_src}/Varquez_etal_2021/AHE_2010_08_average_fix").rename("AHF_08")
        #     ahf09 = ee.Image(f"{ee_ahf_src}/Varquez_etal_2021/AHE_2010_09_average_fix").rename("AHF_09")
        #     ahf10 = ee.Image(f"{ee_ahf_src}/Varquez_etal_2021/AHE_2010_10_average_fix").rename("AHF_10")
        #     ahf11 = ee.Image(f"{ee_ahf_src}/Varquez_etal_2021/AHE_2010_11_average_fix").rename("AHF_11")
        #     ahf12 = ee.Image(f"{ee_ahf_src}/Varquez_etal_2021/AHE_2010_12_average_fix").rename("AHF_12")
        #
        #     # Merge monthly as bands to file
        #     ahf = ahf01.addBands(ahf02).addBands(ahf03).addBands(ahf04) \
        #         .addBands(ahf05).addBands(ahf06).addBands(ahf07) \
        #         .addBands(ahf08).addBands(ahf09).addBands(ahf10) \
        #         .addBands(ahf11).addBands(ahf12)
        #
        # else:
        #     # Get ahf image
        #     ahf = ee.Image(f"{ee_ahf_src}/{ahf_products[ahf_source]}") \
        #         .rename('AHF')

        # Get world cover 10m land cover fractions
        luc = ee.ImageCollection("ESA/WorldCover/v100")\
            .first()\
            .rename('LUC')

        # Get Copernicus discrete land cover for tree types (broadleaf/evergreen)
        # Data: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global
        ft = ee.Image(ee.ImageCollection("COPERNICUS/Landcover/100m/Proba-V-C3/Global") \
          .filterDate('2019-01-01', '2020-01-01') \
          .first() \
          .select('forest_type'))

        # Get forect canopy height, from 2019.
        # See also: https://glad.earthengine.app/view/global-forest-canopy-height-2019
        gcfh_proj = ee.ImageCollection('users/potapovpeter/GEDI_V25_Boreal') \
            .first() \
            .projection()
        gcfh = ee.ImageCollection('users/potapovpeter/GEDI_V25_Boreal') \
            .merge(ee.ImageCollection('users/potapovpeter/GEDI_V27')) \
            .mosaic() \
            .rename('GCFH') \
            .setDefaultProjection(gcfh_proj)

        # S2 urban probability layer, as proxy for building footprints??
        # FAILS WHEN DOWNLOADING ... NOT SURE WHY?
        # s2up_proj = ee.Image("projects/WUDAPT/LULC/GHS_BUILT_S2comp2018_GLOBE_R2020/10S_PROB") \
        #     .projection()
        # s2up = ee.ImageCollection("projects/WUDAPT/LULC/GHS_BUILT_S2comp2018_GLOBE_R2020") \
        #     .mosaic() \
        #     .rename('S2UP') \
        #     .setDefaultProjection(s2up_proj)


        # merge as one image
        # For now, take AHF out.
        #.addBands(ahf)
        # .addBands(s2up)

        img = luc \
            .addBands(ft) \
            .addBands(gcfh) \
            .clip(roi) \
            .toInt()

        bands = img.bandNames().getInfo()
        print(bands)

        # Create download path
        url = img.getDownloadUrl({'bands': bands, 'region': roi})

        # Create path to store img .zip file
        img_path = info['odir'] / "ee_preprocessor.zip"

    # Download the extracted information
    try:
        print(f'Downloading {data_source} data to drive ...')
        print(img_path)
        with open(img_path, "wb") as file:
            # get request
            response = get(url)
            # write to zip file on local drive
            file.write(response.content)

        # Check whether zip file is exists and is valid
        if zp.is_zipfile(img_path) and os.path.isfile(img_path):

            # If fine, unpack to input folder
            os.makedirs(info['odir'], exist_ok=True)
            with zp.ZipFile(img_path, "r") as zip_ref:
                zip_ref.extractall(info['odir'])

            # Remove zip if LCZ map. tif exists
            os.remove(img_path)

            print(f"{data_source} downloaded from EE and extracted in: {info['odir']}")

        else:
            print(f"{img_path} does not exist or is not a valid zip file.")

    # Will fail if image is too large
    # INFO: To download via link: Total request size
    # must be less than or equal to 50331648 bytes.
    except Exception:
        err = traceback.format_exc()
        print(f'FAILED: \n{err}')
        raise


def main() -> int:
    #ee.Authenticate()
    ee.Initialize()

    # Mock-up
    city = 'AU-Preston'
    clat = -37.7306
    clon = 145.0145

    # Test pixel with more different LCZ classes around it
    # clon = 145.01191
    # clat = -37.80972
    dxy = 0.01

    # where ee-processor output is stored
    odir = Path(os.path.join(
        '/data',
        city,
        'input'
    ))

    info = {
        'xmin': clon-dxy,
        'xmax': clon+dxy,
        'ymin': clat-dxy,
        'ymax': clat+dxy,
        'odir': odir,
    }
    # Get the LCZ map from EE
    get_ee_data(info=info, data_source='LCZ')

    # Get the data from EE
    get_ee_data(info=info, data_source='POPDEN')

    # Get the data from EE
    get_ee_data(info=info, data_source='OTHER')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
