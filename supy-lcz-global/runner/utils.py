from __future__ import annotations

import argparse
import os
os.environ['USE_PYGEOS'] = '0'
import traceback
import zipfile as zp
from pathlib import Path
from typing import Any
from typing import Hashable
from typing import Iterator
from typing import Literal

from atmosp import calculate as ac
from collections import Counter
import ee
import geopandas as gpd
import georasters as gr
import netCDF4 as nc
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from pyproj import CRS
from pyproj import Transformer
from rasterio.warp import reproject, Resampling
from requests import get
from shapely.geometry import Point
from shapely.geometry import Polygon
import rioxarray as rxr
import xarray as xr
import supy
from datetime import datetime, timedelta
import warnings

ee.Initialize()

def get_city_from_site_list(args: argparse.Namespace) -> pd.Series:

    # check if a custom sitelist was set and read it
    if args.sitelist is not None:
        fn_sitelist = args.sitelist
    else:
        fn_sitelist = 'sitelist_urbanplumber'

    site_list = pd.read_csv(f'resources/{fn_sitelist}.csv')
    # this should always only be a one row df!
    return site_list[site_list['sitename'] == args.city].iloc[0]

class Buffer:
    def __init__(self, gdf: gpd.GeoDataFrame, crs: CRS) -> None:
        self.gdf = gdf
        self.crs = crs

    @classmethod
    def from_point(
            cls,
            *,
            lon: float,
            lat: float,
            buffer_rad: float,
            target_crs: CRS = CRS('EPSG:4326'),
    ) -> Buffer:
        crs_dict = {
            'proj': 'utm',
            'zone': int(np.round((183 + lon) / 6)),
            'south': lat < 0,
        }
        crs = CRS.from_dict(crs_dict)
        to_utm = Transformer.from_crs(crs_from='EPSG:4326', crs_to=crs)
        x_m, y_m = to_utm.transform(xx=lat, yy=lon)
        pt = Point(x_m, y_m).buffer(buffer_rad)
        gdf = gpd.GeoDataFrame({'geometry': [pt]})
        gdf.index.name = 'id'
        # the stupid georasters thing does only work if there is some column
        gdf['some_col'] = 1
        gdf = gdf.set_crs(crs)
        gdf = gdf.to_crs(target_crs)
        return cls(gdf=gdf, crs=target_crs)

    @property
    def bounds(self) -> NDArray[np.float_]:
        """Returns an array containing ``minx``, ``miny``, ``maxx``, ``maxy``"""
        return self.gdf.geometry.total_bounds


class Grid:
    def __init__(
            self,
            gdf: gpd.GeoDataFrame,
            shape: tuple[int, int],
            step: float,
            crs: CRS,
    ) -> None:
        self.gdf = gdf
        self.shape = shape
        self.step = step
        self.crs = crs

    @property
    def bounds(self) -> NDArray[np.float_]:
        """Returns an array containing ``minx``, ``miny``, ``maxx``, ``maxy``"""
        return self.gdf.geometry.total_bounds

    @classmethod
    def from_point(
            cls,
            *,
            lon: float,
            lat: float,
            nx: int,
            dx: float,
            target_crs: CRS = CRS('EPSG:4326'),
    ) -> Grid:
        crs_dict = {
            'proj': 'utm',
            'zone': int(np.round((183 + lon) / 6)),
            'south': lat < 0,
        }
        crs = CRS.from_dict(crs_dict)
        to_utm = Transformer.from_crs(crs_from='EPSG:4326', crs_to=crs)
        x_m, y_m = to_utm.transform(xx=lat, yy=lon)

        y_m_max = y_m + (nx / 2 * dx)
        y_m_min = y_m_max - ((nx - 1) * dx)
        x_m_max = x_m + (nx / 2 * dx)
        x_m_min = x_m_max - ((nx - 1) * dx)

        y_m = np.linspace(y_m_min, y_m_max, nx)
        x_m = np.linspace(x_m_min, x_m_max, nx)
        xx, yy = np.meshgrid(y_m, x_m)
        polygons = (
            Polygon(
                [(y - dx, x), (y - dx, x - dx), (y, x - dx), (y, x)],
            ) for x, y in zip(xx.ravel(), yy.ravel())
        )
        grid = gpd.GeoDataFrame({'geometry': polygons})
        grid.index.name = 'id'
        # the stupid georasters thing does only work if there is some column
        grid['some_col'] = 1
        grid = grid.set_crs(crs)
        grid = grid.to_crs(target_crs)
        return cls(gdf=grid, shape=(nx, nx), step=dx, crs=target_crs)

    @classmethod
    def from_polygon(
            cls,
            *,
            polygon: Polygon,
            nx: int,
            target_crs: CRS = CRS('EPSG:4326'),
    ) -> Grid:
        lon = polygon.centroid.x
        lat = polygon.centroid.y

        crs_dict = {
            'proj': 'utm',
            'zone': int(np.round((183 + lon) / 6)),
            'south': lat < 0,
        }
        crs = CRS.from_dict(crs_dict)
        to_utm = Transformer.from_crs(crs_from='EPSG:4326', crs_to=crs)
        min_corner = polygon.bounds[:2]
        max_corner = polygon.bounds[2:]

        min_corner_m, max_corner_m = (
            to_utm.transform(
                xx=y, yy=x,
            ) for x, y in (min_corner, max_corner)
        )
        x_m_min, y_m_min = min_corner_m
        x_m_max, y_m_max = max_corner_m

        x_step = (x_m_max - x_m_min) / nx
        y_step = (y_m_max - y_m_min) / nx

        # if not square, take the smaller width to make it square and fit
        # into the defined polygon
        if x_step < y_step:
            dx = x_step
        else:
            dx = y_step

        x_m, y_m = to_utm.transform(xx=lat, yy=lon)

        y_m_max = y_m + (nx / 2 * dx)
        y_m_min = y_m_max - ((nx - 1) * dx)
        x_m_max = x_m + (nx / 2 * dx)
        x_m_min = x_m_max - ((nx - 1) * dx)

        y_m = np.linspace(y_m_min, y_m_max, nx)
        x_m = np.linspace(x_m_min, x_m_max, nx)
        xx, yy = np.meshgrid(y_m, x_m)
        polygons = (
            Polygon(
                [(y - dx, x), (y - dx, x - dx), (y, x - dx), (y, x)],
            ) for x, y in zip(xx.ravel(), yy.ravel())
        )
        grid = gpd.GeoDataFrame({'geometry': polygons})
        grid = grid.set_crs(crs)
        grid = grid.to_crs(target_crs)
        return cls(gdf=grid, shape=(nx, nx), step=dx, crs=target_crs)

    def to_file(self, filename: str, **kwargs: Any) -> None:
        self.gdf.to_file(filename=filename, **kwargs)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Grid):
            return self.gdf.equals(other.gdf)
        else:
            return False

    def __iter__(self) -> Iterator[tuple[Hashable, pd.Series]]:
        yield from self.gdf.iterrows()

    def __len__(self) -> int:
        return len(self.gdf)

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}:\n'
            f'- shape: {self.shape}\n'
            f'- step: {self.step:.5f} m\n'
            f'- crs: {self.crs!r}\n'
            f"{' gdf '.center(78, '-')}\n"
            f'{self.gdf!r}\n'
        )


# Define region of interest
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

        # # Get population density, from 2020 (# people / km2).
        # # Data: https://developers.google.com/earth-engine/datasets/catalog/CIESIN_GPWv411_GPW_UNWPP-Adjusted_Population_Density
        # # Too coarse, with too high values across Amsterdam??
        # popden = ee.ImageCollection("CIESIN/GPWv411/GPW_UNWPP-Adjusted_Population_Density") \
        #     .filterDate('2020-01-01', '2021-01-01') \
        #     .first() \
        #     .select('unwpp-adjusted_population_density') \
        #     .rename('POPDEN')

        # # Get population density, from 2015 (# people per cell).
        # # Data: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2016_POP_GPW_GLOBE_V1
        # # 250m resolution, in "Number of people per cell"
        # popden = ee.ImageCollection('JRC/GHSL/P2016/POP_GPW_GLOBE_V1') \
        #     .filterDate('2015-01-01', '2015-12-31') \
        #     .first() \
        #     .select('population_count') \
        #     .setDefaultProjection(crs='EPSG:4326',scale=250) \
        #     .rename('POPDEN')
        popden = ee.Image('JRC/GHSL/P2023A/GHS_POP/2020') \
            .select('population_count') \
            .setDefaultProjection(crs='EPSG:4326',scale=250) \
            .rename('POPDEN')

        # Updated GHSL-Pop data, from 2020 (# people per cell).
        # Data: https://ghsl.jrc.ec.europa.eu/download.php?ds=pop (put on GEE)
        # Documentation: https://ghsl.jrc.ec.europa.eu/documents/GHSL_Data_Package_2023.pdf?t=1683540422
        # 100m resolution, Mollweide, valid for 2020
        # popden_img_id = 'projects/WUDAPT/GHSL/GHS_POP_E2020_GLOBE_R2022A_54009_100_V1_0'
        # popden_img_id = 'projects/WUDAPT/GHSL/GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0'
        # popden = ee.Image(popden_img_id)  \
        #     .setDefaultProjection(crs='EPSG:4326',scale=100) \
        #     .rename('POPDEN')

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

        # merge as one image
        # For now, take AHF out.
        #.addBands(ahf)

        img = luc \
            .addBands(ft) \
            .addBands(gcfh) \
            .clip(roi) \
            .toInt()

        # Test for file size limits
        # img = gcfh \
        #     .clip(roi) \
        #     .toInt()

        bands = img.bandNames().getInfo()

        # Create download path
        url = img.getDownloadUrl({'bands': bands, 'region': roi})

        # Create path to store img .zip file
        img_path = info['odir'] / "ee_preprocessor.zip"

    # Download the extracted information
    try:
        print(f" -----> Downloading {data_source} data from Google's Earth Engine ...")
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

            print(f"     |-> {data_source} downloaded from GEE and extracted in: {info['odir']}")

        else:
            print(f"     |-> WARNING: {img_path} does not exist or is not a valid zip file.")

    # Will fail if image is too large
    # INFO: To download via link: Total request size
    # must be less than or equal to 50331648 bytes.
    except Exception:
        err = traceback.format_exc()
        print(f'FAILED: \n{err}')
        raise

def _find_lcz_mode_neighbour(lcz_arr, xi, yi) -> int():

    '''Helper function to find mode around missing LCZ pixel'''

    # Initialize search window (sw) and modal value
    sw = 1
    lcz_mode = np.nan

    while np.isnan(lcz_mode):

        # Need to take into account that 0 pixel can be at the edge
        if xi == 0:
            lcz_tmp = lcz_arr[yi - sw:yi + (sw + 1), xi:xi + (sw + 1)]
        elif yi == 0:
            lcz_tmp = lcz_arr[yi:yi + (sw + 1), xi - sw:xi + (sw + 1)]
        elif (xi == 0) and (yi == 0):
            lcz_tmp = lcz_arr[yi:yi + (sw + 1), xi:xi + (sw + 1)]
        else:
            lcz_tmp = lcz_arr[yi - sw:yi + (sw + 1), xi - sw:xi + (sw + 1)]

        # Drop the zeros
        lcz_tmp = lcz_tmp[np.nonzero(lcz_tmp)]

        # Count number of unique values
        c = Counter(lcz_tmp)
        lcz_mode_tmp = c.most_common(1)

        # Check if mode is really unique?
        # As it is possible that more than 1 LCZs have highest frequency
        if list(c.values()).count(lcz_mode_tmp[0][1]) > 1:
            sw += 1
        else:
            lcz_mode = lcz_mode_tmp[0][0]

    # Returns an integer
    return lcz_mode

def check_lcz_for_zero(fn_lcz) -> None:

    # Open the LCZ map
    ds_lcz = rxr.open_rasterio(fn_lcz)

    # Get the lcz data
    lcz_arr = ds_lcz.data[0,:,:]

    # Positions of LCZ pixels with no (0) value, first y, then x
    zero_lczs = np.where(lcz_arr == 0)

    # If positions exist, fill those with modal LCZ value
    if len(zero_lczs[0]) > 0:

        # Loop over coordinates to fill map
        for xi, yi in zip(zero_lczs[1],zero_lczs[0]):

            lcz_mode = _find_lcz_mode_neighbour(lcz_arr, xi, yi)
            lcz_arr[yi, xi] = lcz_mode

        # Put data back into original LCZ map
        ds_lcz.data[0,:,:] = lcz_arr

        # Overwrite downloaded map.
        ds_lcz.rio.to_raster(fn_lcz)

        print(f"     |-> {len(zero_lczs[0])} LCZ pixels with 0's fixed")

    else:
        print(f"     |-> No LCZ pixels with 0's")

    return

def get_popdensity(
        site_info: dict[str, Any],
        roi: Grid | Buffer,
        args: argparse.Namespace,
) -> float:

    '''
    Helper function to get the population density for the ROI.

    ** No longer used **:
        Input data: GPWv411: UN-Adjusted Population Density (Gridded Population of the World Version 4.11)
        Dimension: persons / km2
        Resolution: 1 km
        Web: https://developers.google.com/earth-engine/datasets/catalog/CIESIN_GPWv411_GPW_UNWPP-Adjusted_Population_Density
        Output: pop density in persons / km2

    ** OLD GHSL **:
        Input data: GHSL: Global Human Settlement Layers, Population Grid 1975-1990-2000-2015 (P2016)
        Dimension: persons per grid cell
        Resolution: 250m
        Version: 2016
        Web: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2016_POP_GPW_GLOBE_V1#description
        Output: pop density in persons / 6.25 ha

    ** NEW GHSL **:
        Input data: GHS-POP R2022A - GHS population grid multitemporal (1975-2030)
        Dimension: persons per grid cell
        Resolution: 100m
        Version: 2022
        Web: https://ghsl.jrc.ec.europa.eu/ghs_pop2022.php
        Output: pop density in persons / 1 ha
    '''

    # read in lcz raster and select first band
    # popden_file = Path('data', site_info['sitename'], 'input',  args.run_type,
    #                    'gpw_v4_population_density_adjusted_to_2015_unwpp_'
    #                    'country_totals_rev11_2020_30_sec.POPDEN.tif')
    popden_file = Path('data', site_info['sitename'], 'input',  args.run_type,
                       '2020.POPDEN.tif')
    # popden_file = Path('data', site_info['sitename'], 'input',  args.run_type,
    #                    'GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0.POPDEN.tif')
    grd_popden = gr.from_file(popden_file.as_posix())

    # Clip from Buffer or Grid.
    # For buffer, select pixels that fall WITHIN circular buffer
    if isinstance(roi, Buffer):
        df_popden_clip = grd_popden.clip(roi.gdf, keep=True, all_touched=False)
        dct = {
            0: df_popden_clip.iloc[0].GeoRaster.to_pandas()
        }
        df_popden_mean = pd.concat(dct)['value'].mean()

    # For grid, select all pixels that touch the grid
    if isinstance(roi, Grid):
        df_popden_clip = grd_popden.clip(roi.gdf, keep=True, all_touched=True)
        dct = {
            roi: x.GeoRaster.to_pandas().value_counts('value')
            for roi, x in df_popden_clip.iterrows()
        }
        df_popden_mean = pd.concat(dct).reset_index().groupby('level_0').mean()['value']
        df_popden_mean.index = df_popden_mean.index.astype(int)
        df_popden_mean.sort_index(inplace=True)

    return df_popden_mean


def _reproject_lcz(ds_src, ds_dest):

    '''
    Helper function to reproject LCZ map to target grid
    '''

    out = reproject(
        ds_src.data,
        ds_dest.data,
        src_transform=ds_src.rio.transform(),
        src_crs=ds_src.rio.crs,
        dst_transform=ds_dest.rio.transform(),
        dst_crs=ds_dest.rio.crs,
        resampling=Resampling.nearest
    )

    # Convert to dataarray that contains coordinates
    ds_out = ds_dest.copy()
    ds_out.data = out[0]

    return ds_out


def update_supy_lcz_conversion_table(
        site_info: pd.Series,
        roi: Grid | Buffer,
        df_lcz_rule: pd.DataFrame,
        args: argparse.Namespace,
) -> pd.DataFrame:

    '''
    Update LCZ table, per LCZ class available in footprint, for:
        1) pervious fraction
        2) deciduous / evergreen tree fractions
        3) mean vegetation height

    Note: only valid for Buffer? How to do this for the Grid?
    '''

    print(f" -----> Updating the lcz_to_suews_conversion table ...")

    #TODO: How to do this for a Grid?
    #Read the data and clip tif files according to Buffer
    #LCZ map
    lcz_file = Path('data', site_info['sitename'], 'input',  args.run_type, 'download.LCZ_Filter.tif')
    lcz = rxr.open_rasterio(lcz_file)[0, :, :] \
        .rio.clip(roi.gdf.geometry, all_touched=True)
    lczm = lcz.where(lcz != lcz.attrs['_FillValue'])

    # LUC
    luc_file = Path('data', site_info['sitename'], 'input',  args.run_type, '2020.LUC.tif')
    luc = rxr.open_rasterio(luc_file)[0, :, :] \
        .rio.clip(roi.gdf.geometry, all_touched=True)
    lucm = luc.where(luc != luc.attrs['_FillValue'])

    # Tree type
    tt_file = Path('data', site_info['sitename'], 'input',  args.run_type, '2020.forest_type.tif')
    tt = rxr.open_rasterio(tt_file)[0, :, :] \
        .rio.reproject("EPSG:4326") \
        .rio.clip(roi.gdf.geometry, all_touched=True)
    ttm = tt.where(tt != tt.attrs['_FillValue'])

    # Tree height
    th_file = Path('data', site_info['sitename'], 'input',  args.run_type, '2020.GCFH.tif')
    th = rxr.open_rasterio(th_file)[0, :, :] \
        .rio.clip(roi.gdf.geometry, all_touched=True)
    thm = th.where(th != th.attrs['_FillValue'])

    # Reproject the LCZ map to required grids
    lczm_luc = _reproject_lcz(ds_src=lczm, ds_dest=lucm.copy())
    lczm_ttm = _reproject_lcz(ds_src=lczm, ds_dest=ttm.copy())
    lczm_thm = _reproject_lcz(ds_src=lczm, ds_dest=thm.copy())

    # Check available LCZ classes in footprint, that are not nan
    lcz_unique = np.unique(lczm)

    # It is possible that LCZ 0 occurs, referring to masked pixels in the map
    # Set those to nan as well
    # Also neglect LCZ 17 - water, as no conversion update should be done here.
    lcz_unique = lcz_unique.astype('float')
    lcz_unique[lcz_unique == 0] = np.nan
    lcz_unique[lcz_unique == 17] = np.nan
    lcz_unique = lcz_unique[~np.isnan(lcz_unique)]

    # Add info to conversion table for each of the available LCZ classes.
    for i in lcz_unique:

        # make sure i is an integer?
        i = int(i)

        # 1. The land cover fractions: tree, grass, bare and water
        luc_lcz_i = xr.where(lczm_luc == i, lucm, np.nan).data.flatten()

        # non-built fractions, including:
        #         # Tree cover(10),
        #         # shrubland(20, assigned to grassland),
        #         # grassland(30),
        #         # cropland(40, assigned to grassland),
        #         # Bare / sparse vegetation(60),
        #         # Permanent water bodies(80):
        worldcover_nonbuilt_classes = [10, 20, 30, 40, 60, 80]

        # Count all pixels with these classes
        nonbuilt_cnt = sum(np.in1d(luc_lcz_i, worldcover_nonbuilt_classes))

        if not nonbuilt_cnt == 0:

            # Composed of:
            tree_fr = sum(np.in1d(luc_lcz_i, [10])) / nonbuilt_cnt
            grass_fr = sum(np.in1d(luc_lcz_i, [20, 30, 40])) / nonbuilt_cnt
            bare_fr = sum(np.in1d(luc_lcz_i, [60])) / nonbuilt_cnt
            water_fr = sum(np.in1d(luc_lcz_i, [80])) / nonbuilt_cnt
            #print(tree_fr, grass_fr, bare_fr, water_fr)

            # These fractions need to be re-scaled to complement the
            # available impervious fractions (= paved + buildings)
            lcz_i_imp = df_lcz_rule.loc[["Paved (-)", "Buildings (-)"], f"LCZ{i}"].sum()

            # Put new fractions in df_lcz_rule
            # TODO: is this the behaviour we'd like to see??
            df_lcz_rule.loc[["Grass (-)"], f"LCZ{i}"] = \
                grass_fr * (1 - lcz_i_imp)
            df_lcz_rule.loc[["Bare soil (-)"], f"LCZ{i}"] = \
                bare_fr * (1 - lcz_i_imp)
            df_lcz_rule.loc[["Water (-)"], f"LCZ{i}"] = \
                water_fr * (1 - lcz_i_imp)

            # For trees, initially put all in deciduous
            # This might be adjusted in a second step?
            df_lcz_rule.loc[["Deciduous trees (-)"], f"LCZ{i}"] = \
                tree_fr * (1 - lcz_i_imp)

            # Check if sum equals 1?
            supy_fractions = [
                "Paved (-)",
                "Buildings (-)",
                "Grass (-)",
                "Deciduous trees (-)",
                "Evergreen trees (-)",
                "Bare soil (-)",
                "Water (-)",
            ]
            if np.round(df_lcz_rule.loc[supy_fractions, f"LCZ{i}"].sum(),5) == 1.0:
                print(f"     |-> Fractions sum to 1 for LCZ {i}")
            else:
                print(f"     |-> WARNING for LCZ {i}: the sum of the "
                      f"new fractions do not sum to 1.")

        # 2. The tree types
        ttm_lcz_i = xr.where(lczm_ttm == i, ttm, np.nan).data.flatten()

        # For testing
        # ttm_lcz_i = np.array([1,1, 1, 1, 2, 3, 4, 4, 4, 4,4,4,4,4,4, 5, np.nan, np.nan])

        # Set 0 (unknown) to nan
        ttm_lcz_i = ttm_lcz_i.astype('float')
        ttm_lcz_i[ttm_lcz_i == 0] = np.nan  # or use np.nan

        if np.isnan(ttm_lcz_i).all():
            print(f"     |-> No tree type data available for LCZ {i}")

        else:

            # array to test
            copernicus_tree_classes = [1, 2, 3, 4, 5]
            tree_count = sum(np.in1d(ttm_lcz_i, copernicus_tree_classes))

            # Composed of:

            # Mixed is half added to evergeen and half to boadleaf
            mixtree = sum(np.in1d(ttm_lcz_i, [5.]))

            # Evergreen or broadleaf?
            evetree = (sum(np.in1d(ttm_lcz_i, [1., 2.])) + (mixtree / 2)) / tree_count
            dectree = (sum(np.in1d(ttm_lcz_i, [3., 4.])) + (mixtree / 2)) / tree_count

            # Now scale decidous tree fraction in df_lcz_rule
            df_dectree = float(df_lcz_rule.loc[["Deciduous trees (-)"], f"LCZ{i}"])
            df_lcz_rule.loc[["Deciduous trees (-)"], f"LCZ{i}"] = df_dectree * dectree
            df_lcz_rule.loc[["Evergreen trees (-)"], f"LCZ{i}"] = df_dectree * evetree

            if np.round(df_lcz_rule.loc[supy_fractions, f"LCZ{i}"].sum(),5) == 1.0:
                print(f"     |-> Fractions sum to 1 after assigning tree types for LCZ {i}")
            else:
                print(f"     |-> WARNING for LCZ {i}: the sum of the new fractions do "
                      f"not sum to 1 after assigning tree types.")

        # 3. Assign tree height
        thm_lcz_i = xr.where(lczm_thm == i, thm, np.nan).data.flatten()

        # Set 0 (unknown) to nan
        thm_lcz_i = thm_lcz_i.astype('float')
        thm_lcz_i[thm_lcz_i == 0] = np.nan

        # Get the mean over the footprint
        warnings.filterwarnings(action='ignore', message='Mean of empty slice')
        tree_height_mean = np.nanmean(thm_lcz_i)

        # Assign to df_lcz_rule
        if np.isnan(tree_height_mean):
            print(f"     |-> No tree height data available for LCZ {i}")
        else:
            print(f"     |-> Average tree height added for LCZ {i}")
            df_lcz_rule.loc[["Mean vegetation height (m)"], f"LCZ{i}"] = tree_height_mean

    return df_lcz_rule


def gen_era5_forcing(
        args: argparse.Namespace,
        site_info: pd.Series,
        dir_save: Path,
        spinup_days: int,
):

    # Add a day before and at the end, might be needed when converting to Local Time?
    if args.do_spinup:
        start_date = pd.to_datetime(
            site_info['time_analysis_start']
        ).date() - timedelta(days=(spinup_days + 2))
    else:
        start_date = pd.to_datetime(
            site_info['time_analysis_start']
        ).date() - timedelta(days=2)
    end_date = pd.to_datetime(
        site_info['time_coverage_end']
    ).date() + timedelta(days=2)

    supy.util.gen_forcing_era5(
        lat_x=float(site_info['latitude']),
        lon_x=float(site_info['longitude']),
        start=start_date,
        end=end_date,
        dir_save=dir_save,
        grid=None,
        hgt_agl_diag=100.0, # Default SUPY value.
        scale=0,
        force_download=True,
        simple_mode=True,
        pressure_level=None,
    )


def _era5land_store_timeseries_to_df(ic, start_date, end_date, aoi, dir_save):

    variables_long = [
        "u_component_of_wind_10m",
        "v_component_of_wind_10m",
        "dewpoint_temperature_2m",
        "surface_pressure",
        "temperature_2m",
        "total_precipitation_hourly",
        "surface_solar_radiation_downwards_hourly",
        "surface_thermal_radiation_downwards_hourly",
        #"surface_latent_heat_flux_hourly",
        #"surface_sensible_heat_flux_hourly",
    ]

    variables_short = ['u10m', 'v10m', 'Td', 'pres',
                       'Tair', 'rain', 'kdown', 'ldown',
                       #'qe', 'qh'
                       ]
    variables_export = ['datetime'] + variables_short

    # Load in image collection and filter by area and date
    # Add few days before and after: change from UTC to LT might require more timesteps?
    era5_land = ic \
        .filterDate(
        ee.Date(start_date).advance(-2, 'day'),
        ee.Date(end_date).advance(2, 'day')) \
        .select(variables_long, variables_short)

    # Select first image to get scale and crs
    imgRep = era5_land.first()

    def _era5land_get_timeseries(image):

        ''' Extract the point-based timeseries as a featurecollection '''
        def set_properties(f):
            return f.set('datetime', image.date().format('YYYY-MM-dd HH:mm:ss'))

        col = image.reduceRegions(
            collection=aoi,
            reducer=ee.Reducer.mean(),
            scale= 500, #imgRep.projection().nominalScale(),
            crs=imgRep.projection().crs()
            ).map(set_properties)

        return ee.FeatureCollection(col)

    results = era5_land.map(_era5land_get_timeseries).flatten()
    # print(results.getInfo())

    # CHECK: https://kaflekrishna.com.np/blog-detail/extraction-raster-values-point-samples-google-earth-engine-gee/
    nested_list = results.reduceColumns(
        ee.Reducer.toList(len(variables_export)),
        variables_export
    ).values().get(0)
    data = nested_list.getInfo()

    # Convert to pandas dataframe
    df = pd.DataFrame(data, columns=variables_export)

    # Save to drive
    OFILE = os.path.join(
        dir_save,
        f"ERA5LAND_{start_date}-{end_date}.csv",
    )
    df.to_csv(OFILE, index=False)


def era5land_check_lsm(site_info, dir_save):

    '''
    Check if the coordinates will contain data, as ERA5-Land has no data
    for pixels with land fraction < 50%:

    Data: https://confluence.ecmwf.int/display/CKB/ERA5-Land%3A+data+documentation
    '''

    # Get the pixel value
    fn_lsm = 'resources/lsm_1279l4_0.1x0.1.grb_v4_unpack.nc'
    ds = xr.open_dataset(fn_lsm)

    # Make longitudes consistent with sitelist [-180 to 180]
    # instead of [0 to 306]
    ds.coords['longitude'] = (ds.coords['longitude'] + 180) % 360 - 180
    ds = ds.sortby(ds['longitude'])

    ds_point = ds.sel(
        longitude=site_info['longitude'],
        latitude=site_info['latitude'],
        method="nearest"
    )
    max_value = float(ds_point.lsm.data)

    # if lsm is < 0.5, check 8 neighbouring pixels, take one with highest lsm value
    if max_value <= 0.5:

        print("     |- Not enough landmass at this coordinate, "
              "looking at neighbouring pixels")

        dxy = 0.15
        dxy_iter = 0

        # Check surroundings pixels with a window.
        # Continue to check as long as no valid pixels are found
        while max_value <= 0.5:

            dxy_iter += 1

            ds_window = ds.sel(
                longitude=slice(
                    (site_info['longitude']-(dxy_iter*dxy)),
                    (site_info['longitude']+(dxy_iter*dxy))
                ),
                latitude=slice(
                    (site_info['latitude']+(dxy_iter*dxy)),
                    (site_info['latitude']-(dxy_iter*dxy))
                ),
            )
            max_value = ds_window.lsm.max()


        # Get the coordinates of this max value pixel
        lon_new = float(ds_window.where(
            ds_window == max_value, drop=True
        ).squeeze().longitude)
        lat_new = float(ds_window.where(
            ds_window == max_value, drop=True
        ).squeeze().latitude)

        print(f"    -- Valid neighbouring pixel found in "
              f"{dxy_iter} iteration(s): "
              f"lat = {np.round(lon_new,4)}, "
              f"lon = {np.round(lat_new,4)}, "
              f"lsm = {np.round(float(max_value),4)}"
              )

    else:
        # Keep original coordinates
        print("     |-> Selected pixel is valid.")
        lon_new = site_info['longitude']
        lat_new = site_info['latitude']

    # Write info to file, remove first if exists
    path_note = dir_save / "ERA5Land_Note_on_coordinates"
    path_note.unlink(missing_ok=True)
    f = open(path_note, "a")
    line_old = f"Original pixel (lon | lat | land fraction): " \
               f"{site_info['longitude']} | {site_info['latitude']} | " \
               f"{float(ds_point.lsm)}"
    line_new = f"New pixel (lon | lat | land fraction): " \
               f"{lon_new} | {lat_new} | {float(max_value)}"
    f.writelines([f"\n{line_old}",f"\n{line_new}"])
    f.close()

    return lon_new, lat_new

def _era5land_get_z0m(lon, lat):

    ''' Get appropriate z0m value for selected land pixel '''

    # Read the vegetation type and cover files
    fn_tvl = 'resources/tvl.nc'
    fn_tvh = 'resources/tvh.nc'
    fn_cvl = 'resources/cvl.nc'
    fn_cvh = 'resources/cvh.nc'

    #xarray.open_mfdataset failed because of different timestamp?
    ds_tvl = xr.open_dataset(fn_tvl).squeeze(dim='time')
    ds_tvh = xr.open_dataset(fn_tvh).squeeze(dim='time')
    ds_cvl = xr.open_dataset(fn_cvl).squeeze(dim='time')
    ds_cvh = xr.open_dataset(fn_cvh).squeeze(dim='time')

    # Combine
    dsv = xr.merge([ds_tvl, ds_tvh, ds_cvl, ds_cvh], compat='override')

    # Make longitudes consistent with sitelist [-180 to 180]
    # instead of [0 to 306]
    dsv.coords['longitude'] = (dsv.coords['longitude'] + 180) % 360 - 180
    dsv = dsv.sortby(dsv['longitude'])

    # Get values for pixel
    dsv_point = dsv.sel(
        longitude=lon,
        latitude=lat,
        method="nearest"
    )

    # Read look-up table for vegetation characteristics
    veg_table = pd.read_csv('resources/ECMWF_IFS_VegetationProperties.csv', index_col=0)

    # get the fractions, as Eq. 8.1 in documentation, and
    # corresponding z0m, based on Eq. 8.5
    if int(np.ceil(dsv_point.tvh.values)) != 0:
        c_veg_h = veg_table.loc[int(np.round(dsv_point.tvh.values, 0)), 'c_veg']
        c_h = float(dsv_point.cvh.values) * c_veg_h
        z0m_c_h = c_h / (np.log(10) / veg_table.loc[int(np.ceil(dsv_point.tvh.values)), 'z0_m']) ** 2
    else:
        z0m_c_h = 0.0

    if int(np.round(dsv_point.tvl.values, 0)) != 0:
        c_veg_l = veg_table.loc[int(np.round(dsv_point.tvl.values, 0)), 'c_veg']
        c_l = float(dsv_point.cvl.values) * c_veg_l
        z0m_c_l = c_l / (np.log(10) / veg_table.loc[int(np.ceil(dsv_point.tvl.values)), 'z0_m']) ** 2
    else:
        z0m_c_l = 0.0

    # aggregated roughness length
    sum_z0m = z0m_c_h + z0m_c_l
    z0ma = (sum_z0m * np.log(10)**2)**0.5

    return z0ma


def gen_era5land_forcing(
        args: argparse.Namespace,
        longitude: float,
        latitude: float,
        site_info: pd.Series,
        dir_save: Path,
        spinup_days: int,
):

    # spin-up needs to be taken into account in time_coverage_start
    if args.do_spinup:
        start_date = pd.to_datetime(
            site_info['time_analysis_start']
        ).date() - timedelta(days=(spinup_days + 2))
    else:
        start_date = pd.to_datetime(
            site_info['time_analysis_start']
        ).date() - timedelta(days=2)
    end_date = pd.to_datetime(
        site_info['time_coverage_end']
    ).date() + timedelta(days=2)

    aoi = ee.Geometry.Point([longitude, latitude])

    # Input data: ERA5-Land hourly
    # https:#developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY
    ic = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY")

    # If time span is too long, it will result in a computation time out.
    # So the request needs to be split in chunks, e.g. per ~ year.
    # Check length of the request in days
    time_span_days = (end_date - start_date).days

    if time_span_days > 365:

        # Initialize chunk start- and end_dates
        start_date_chunk = start_date
        end_date_chunk = start_date_chunk.replace(
            year=start_date_chunk.year+1, month=1, day=1
        )

        while start_date_chunk < end_date:

            # Set end date to final analysis time, for last chunk
            if end_date_chunk > end_date:
                # Need to add one day to end_date, as last day is otherwise missing
                end_date_chunk = end_date + timedelta(days=1)

            # Get the timeseries for this year
            print(f"    -- Retrieving: "
                  f"{start_date_chunk.strftime('%Y-%m-%d')} - "
                  f"{end_date_chunk.strftime('%Y-%m-%d')}")
            _era5land_store_timeseries_to_df(
                ic=ic,
                start_date=start_date_chunk.strftime('%Y-%m-%d'),
                end_date=end_date_chunk.strftime('%Y-%m-%d'),
                aoi=aoi,
                dir_save=dir_save,
            )

            # Reset start_date to next chunck
            start_date_chunk = end_date_chunk
            end_date_chunk = start_date_chunk.replace(
                year=start_date_chunk.year+1, month=1, day=1
            )

    else:
        # Need to add one day to end_date, as last day is otherwise missing
        print(f"    -- Retrieving: "
              f"{start_date.strftime('%Y-%m-%d')} - "
              f"{end_date.strftime('%Y-%m-%d')}")
        _era5land_store_timeseries_to_df(
            ic=ic,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            aoi=aoi,
            dir_save=dir_save,
        )

def _diag_era5land(z0m, pres_z0, uv10, t2, q2, z):

    # constants
    # environmental lapse rate [K m^-1]
    env_lapse = 6.5 / 1000.0
    # gravity [m s^-2]
    grav = 9.80616
    # Gas constant for dry air [J K^-1 kg^-1]
    rd = 287.04

    # correct temperature using lapse rate
    t_z = t2 - (z - 2) * env_lapse

    # barometric equation with varying temperature:
    # (https://en.wikipedia.org/wiki/Barometric_formula)
    p_z = pres_z0 * (t_z / t2) ** (grav / (rd * env_lapse))

    # correct humidity assuming invariable relative humidity
    RH_z = ac("RH", qv=q2, p=pres_z0, T=t2) + 0 * t_z
    #q_z = ac("qv", RH=RH_z, p=p_z, T=t_z) + 0 * t_z

    # correct wind speed using log law; assuming neutral condition (without stability correction)
    uv_z = uv10 * (np.log((z + z0m) / z0m) / np.log((10 + z0m) / z0m))

    return uv_z, t_z, RH_z, p_z # q_z


def format_era5land_forcing(lon, lat, dir_save, hgt_agl_diag=100):

    era5land_forcings = sorted(dir_save.glob('ERA5LAND_*.csv'))
    df_forcing = pd.concat(
        pd.read_csv(f, index_col=0, parse_dates=True)
        for f in era5land_forcings
    )

    # Make a copy to work with
    df_forcing_format = df_forcing.copy()

    # Prepare all for diagnostics at height hgt_agl_diag=100 m (default)

    # Get the aggregated surface roughness [m]
    z0m = _era5land_get_z0m(lon, lat)
    #print(f"    -----> z0m: {z0m}")

    # surface level atmospheric pressure
    pres_z0 = df_forcing_format.pres

    # wind speed
    u10 = df_forcing_format.u10m
    v10 = df_forcing_format.v10m
    uv10 = np.sqrt(u10**2 + v10**2)

    # air temperature
    t2 = df_forcing_format.Tair

    # dew point
    d2 = df_forcing_format.Td

    # specific humidity
    q2 = ac("qv", Td=d2, T=t2, p=pres_z0)

    # Diagnose the properties
    uv_z, t_z, RH_z, p_z = _diag_era5land(
        z0m=z0m,
        pres_z0=pres_z0,
        uv10=uv10,
        t2=t2,
        q2=q2,
        z=hgt_agl_diag,
    )

    # Put diagnosed into in dataframe, adjust existing columns
    # Mean wind speed U
    df_forcing_format.loc[:, "U"] = uv_z
    df_forcing_format.drop(['u10m', 'v10m'], axis=1, inplace=True)

    # convert energy fluxes: [J m-2] to [W m-2]
    #df_forcing_format.loc[:, ["kdown", "ldown", "qh", "qe"]] /= 3600
    df_forcing_format.loc[:, ["kdown", "ldown"]] /= 3600

    # reverse the sign of qh and qe
    #df_forcing_format.loc[:, ["qh", "qe"]] *= -1

    # convert rainfall: from [m] to [mm]
    df_forcing_format.loc[:, "rain"] *= 1000

    # Set diagnosed bulb temperature in degC
    df_forcing_format.loc[:, "Tair"] = t_z - 273.15

    # Set diagnosed relative humidity
    df_forcing_format.loc[:, "RH"] = RH_z
    df_forcing_format.drop(['Td'], axis=1, inplace=True)

    # convert diagnosed pressure: [Pa] to [kPa]
    df_forcing_format.loc[:, "pres"] = p_z / 1000

    dict_var_type_forcing = {
        "iy": "time",
        "id": "time",
        "it": "time",
        "imin": "time",
        "qn": "avg",
        "qh": "avg",
        "qe": "avg",
        "qs": "avg",
        "qf": "avg",
        "U": "inst",
        "RH": "inst",
        "Tair": "inst",
        "pres": "inst",
        "rain": "sum",
        "kdown": "avg",
        "snow": "inst",
        "ldown": "avg",
        "fcld": "inst",
        "Wuh": "sum",
        "xsmd": "inst",
        "lai": "inst",
        "kdiff": "avg",
        "kdir": "avg",
        "wdir": "inst",
        "isec": "time",
    }

    col_suews = list(dict_var_type_forcing.keys())[:-1]

    df_forcing_format = df_forcing_format.reindex(col_suews, axis=1)

    df_forcing_format = df_forcing_format.assign(
        iy=df_forcing_format.index.year,
        id=df_forcing_format.index.dayofyear,
        it=df_forcing_format.index.hour,
        imin=df_forcing_format.index.minute,
    )

    # corrections
    df_forcing_format.loc[:, "RH"] = df_forcing_format.loc[:, "RH"].where(
        df_forcing_format.loc[:, "RH"].between(0.001, 105), 105
    )
    df_forcing_format.loc[:, "kdown"] = df_forcing_format.loc[:, "kdown"].where(
        df_forcing_format.loc[:, "kdown"] > 0, 0
    )

    # trim decimals
    df_forcing_format.iloc[:, 4:] = df_forcing_format.iloc[:, 4:].round(2)

    # coerce integer
    df_forcing_format = df_forcing_format.astype(
        {"iy": "int32", "id": "int32", "it": "int32", "imin": "int32"}
    )

    # Remove duplicate timestamps
    df_forcing_format = df_forcing_format[~df_forcing_format.index.duplicated(keep='first')]

    # replace nan with -999
    df_forcing_format = df_forcing_format.replace(np.nan, -999).asfreq("1h")

    # split into years
    idx_grid = df_forcing_format.index
    grp_year = df_forcing_format.groupby(idx_grid.year)

    #lat = site_info['latitude']
    #lon = site_info['longitude']
    # Use coordinates of selected ERA5Land pixel
    lat = np.round(lat, 2)
    lon = np.round(lon, 2)

    s_lat = f"{lat}N" if lat >= 0 else f"{-lat}S"
    s_lon = f"{lon}E" if lon >= 0 else f"{-lon}W"

    for year in grp_year.groups:
        df_year = grp_year.get_group(year)
        idx_year = df_year.index
        s_year = idx_year[0].year
        s_freq = idx_year.freq / pd.Timedelta("1T")
        s_fn = f"ERA5LAND_UTC_{s_lat}-{s_lon}_{s_year}_data_{s_freq:.0f}.txt"
        path_fn = dir_save / s_fn
        df_year.to_csv(path_fn, sep=" ", index=False)


# def _resample_linear_inst(data_raw_inst, tstep_in, tstep_mod):
#
#     ''' Resample input forcing with instantaneous values by linear interpolation'''
#
#     # downscale input data to desired time step
#     # downscale input data to desired time step
#     data_raw_tstep = data_raw_inst.copy()
#
#     # assign a new start with nan
#     t_start = data_raw_inst.index.shift(-tstep_in + tstep_mod, freq="S")[0]
#     t_end = data_raw_inst.index[-1]
#     data_raw_tstep.loc[t_start, :] = np.nan
#     data_raw_tstep.loc[t_end, :] = np.nan
#
#     # re-align the index so after resampling we can have filled heading part
#     data_raw_tstep = data_raw_tstep.sort_index()
#     data_raw_tstep = data_raw_tstep.asfreq(f"{tstep_mod}S").interpolate(method="linear")
#     # fill gaps with valid values
#     data_tstep = data_raw_tstep.copy().bfill().ffill().dropna(how="all")
#
#     return data_tstep
#
# def _resample_stp(data_raw_stp, tstep_in, tstep_mod):
#
#     '''Helper function for average fluxes - stepwise change'''
#
#     # retrieve ending timestamps
#     t_start = data_raw_stp.index.shift(-tstep_in + tstep_mod, freq="S")[0]
#     t_end = data_raw_stp.index[-1]
#     cols =data_raw_stp.columns
#
#     # create new dataframe with model timestep frequency
#     times = pd.date_range(t_start, t_end, freq=f"{tstep_mod}S")
#     data_tstep = pd.DataFrame(index=times, columns=cols)
#
#     # set raw data to model timestep frequency and backfill gaps
#     data_tstep[cols] = data_raw_stp.asfreq(f'{tstep_mod}S').backfill()
#
#     # fill gaps with valid values
#     data_tstep = data_tstep.copy().bfill().ffill().dropna(how="all")
#
#     return data_tstep
#
# def _resample_sum(data_raw_precip, tstep_in, tstep_mod):
#     ratio_precip = 1.0 * tstep_mod / tstep_in
#     data_tstep_precip_adj = ratio_precip * data_raw_precip.copy().shift(
#         -tstep_in + tstep_mod, freq="S"
#     ).resample("{tstep}S".format(tstep=tstep_mod)).mean().interpolate(
#         method="polynomial", order=0
#     )
#     # assign a new start with nan
#     # t_start = data_raw_precip.index.shift(-tstep_in + tstep_mod, freq='S')[0]
#     t_end = data_raw_precip.index[-1]
#     # data_tstep_precip_adj.loc[t_start, :] = np.nan
#     data_tstep_precip_adj.loc[t_end] = np.nan
#     data_tstep_precip_adj = data_tstep_precip_adj.sort_index()
#     data_tstep_precip_adj = data_tstep_precip_adj.asfreq(
#         "{tstep}S".format(tstep=tstep_mod)
#     )
#     data_tstep_precip_adj = data_tstep_precip_adj.fillna(value=0.0)
#     return data_tstep_precip_adj
#
# def resample_forcing_data(data_met_raw, tstep_in, tstep_mod,
#                           lat=51, lon=0, alt=100, timezone=0, kdownzen=0):
#
#     ''' Resample forcing data to the default 300s interval.
#
#     This code is different from SUEWS' default for the instantaneous parameters,
#     as it performs a stepwise interpolation instead of a linear resampling.
#
#     Original code in SUEWS:
#     https://github.com/UMEP-dev/SUEWS/blob/a1e246c01f98f288f04d3b3b9790428b3650a5e4/src/supy/supy/_load.py#L618
#
#     '''
#
#     if tstep_in % tstep_mod != 0:
#         raise RuntimeError(
#             f"`tstep_in` ({tstep_in}) is not divisible by `tstep_mod` ({tstep_mod})"
#         )
#
#     # define data types for different resampling schemes
#     # time: temporal info
#     # avg: average values of period ending at timestamps
#     # inst: instantaneous values at timestamps
#     # sum: sum of period ending at timestamps
#     dict_var_type_forcing = {
#         "iy": "time",
#         "id": "time",
#         "it": "time",
#         "imin": "time",
#         "qn": "avg",
#         "qh": "avg",
#         "qe": "avg",
#         "qs": "avg",
#         "qf": "avg",
#         "U": "inst",
#         "RH": "inst",
#         "Tair": "inst",
#         "pres": "inst",
#         "rain": "sum",
#         "kdown": "avg",
#         "snow": "inst",
#         "ldown": "avg",
#         "fcld": "inst",
#         "Wuh": "sum",
#         "xsmd": "inst",
#         "lai": "inst",
#         "kdiff": "avg",
#         "kdir": "avg",
#         "wdir": "inst",
#         "isec": "time",
#     }
#
#     data_met_raw = data_met_raw.copy()
#     data_met_raw = data_met_raw.replace(-999, np.nan)
#
#     # # this line is kept for occasional debugging:
#     # if logger_supy.level < 20:
#     #     p_data_met_raw = "data_met_raw.pkl"
#     #     data_met_raw.to_pickle(p_data_met_raw)
#     #     logger_supy.debug(f"{p_data_met_raw} has been generated!")
#
#     # linear interpolation:
#     # the interpolation schemes differ between instantaneous and average values
#     # instantaneous:
#     list_var_inst = [
#         var for var, data_type in dict_var_type_forcing.items() if data_type == "inst"
#     ]
#     data_met_tstep_inst = _resample_linear_inst(
#         data_met_raw.filter(list_var_inst), tstep_in, tstep_mod
#     )
#     # average:
#     list_var_stp = [
#         var for var, data_type in dict_var_type_forcing.items() if data_type == "avg"
#     ]
#     data_met_tstep_stp = _resample_stp(
#         data_met_raw.filter(list_var_stp), tstep_in, tstep_mod
#     )
#
#     # distributing interpolation:
#     # sum:
#     list_var_sum = [
#         var for var, data_type in dict_var_type_forcing.items() if data_type == "sum"
#     ]
#     data_met_tstep_sum = _resample_sum(
#         data_met_raw.filter(list_var_sum), tstep_in, tstep_mod
#     )
#
#     # combine the resampled individual dataframes
#     data_met_tstep = (
#         pd.concat([data_met_tstep_inst, data_met_tstep_stp, data_met_tstep_sum], axis=1)
#         .interpolate()
#         .loc[data_met_tstep_inst.index]
#     )
#
#     # adjust solar radiation by zenith correction and total amount distribution
#     if kdownzen == 1:
#         data_met_tstep["kdown"] = resample_kdn(
#             data_met_tstep["kdown"], tstep_mod, timezone, lat, lon, alt
#         )
#
#     # assign temporal info
#     data_met_tstep["iy"] = data_met_tstep.index.year
#     data_met_tstep["id"] = data_met_tstep.index.dayofyear
#     data_met_tstep["it"] = data_met_tstep.index.hour
#     data_met_tstep["imin"] = data_met_tstep.index.minute
#     data_met_tstep["isec"] = data_met_tstep.index.second
#     data_met_tstep = data_met_tstep.filter(list(dict_var_type_forcing.keys()))
#     data_met_tstep = data_met_tstep.replace(np.nan, -999)
#
#     return data_met_tstep

def use_rdp_fractions(
        site_info: dict[str, Any],
        args: argparse.Namespace,
) -> pd.DataFrame:

    # Set all paths to required files
    fn_grid = Path('data', site_info['sitename'], 'input', args.run_type,'roi_grid.shp')
    fn_rdp = Path('data', site_info['sitename'], 'input', args.run_type,'rdp_fractions_norm.nc')
    fn_state = Path('data', site_info['sitename'], 'output', args.run_type,'df_state_uMF_uLCu.pkl')

    # Read and prepare files
    grid = gpd.read_file(fn_grid)
    df_state = pd.read_pickle(fn_state)
    rdp = xr.open_dataset(fn_rdp)
    rdp = rdp.rio.write_crs(grid.crs)
    rdp = rdp.rename({'Lat': 'y', 'Lon': 'x'})

    # Create dataframe to store fractions in, per grid id
    sfr_rdp = [
        'ROAD_N',
        'BLD_N',
        'VEGB_N',
        'VEGH_N',
        'NVEG_N',
        'WATER_N'
    ]
    df_fractions = pd.DataFrame(
        index=df_state.index,
        columns=sfr_rdp
    )

    for i in grid.index:
        for sfr in sfr_rdp:
            df_fractions.loc[i, sfr] = \
                float(rdp.rio.clip(gpd.GeoSeries(grid.geometry[i])).mean()[sfr])

    # Check if fractions round to 1
    fr_sum = df_fractions[df_fractions.sum(axis=1).astype(float).round(2) == 1.0]
    if fr_sum.shape[0] != grid.shape[0]:
        print('ERROR: not all grid cells have fractions that sum to 1')

    # Repurpose the df_fractions: split trees evenly to evergeen and deciduous
    df_fractions['VEGH_N_EVE'] = df_fractions['VEGH_N'] / 2
    df_fractions['VEGH_N_DEC'] = df_fractions['VEGH_N'] / 2

    # Put in state a new state used for the RDP experiment
    df_state_rdp = df_state.copy()

    dict_rule_columns = {
        ('sfr_surf', '(0,)'): 'ROAD_N',
        ('sfr_surf', '(1,)'): 'BLD_N',
        ('sfr_surf', '(4,)'): 'VEGH_N_EVE',
        ('sfr_surf', '(3,)'): 'VEGH_N_DEC',
        ('sfr_surf', '(2,)'): 'VEGB_N',
        ('sfr_surf', '(5,)'): 'NVEG_N',
        ('sfr_surf', '(6,)'): 'WATER_N',
    }
    df_state_rdp.loc[:, dict_rule_columns.keys()] = \
        df_fractions.loc[:, dict_rule_columns.values()].values

    # Save new state to pickle
    # state_file = Path('data', site_info['sitename'], 'output', args.run_type,'df_state_rdp.pkl')
    # df_state_rdp.to_pickle(state_file)

    return df_state_rdp

def get_spinup_state(
        site_info: dict[str, Any],
        df_state: pd.DataFrame,
        df_forcing: pd.DataFrame,
        spinup_days: int,
) -> pd.DataFrame:

    # Store states after spin-up
    # lai_id: https://suews.readthedocs.io/en/latest/related-softwares/supy/data-structure/df_state.html?highlight=state_surf#cmdoption-arg-lai_id
    # soilstore_surf (sss): https://suews.readthedocs.io/en/latest/related-softwares/supy/data-structure/df_state.html?highlight=state_surf#cmdoption-arg-soilstore_surf
    # state_surf (ss): https://suews.readthedocs.io/en/latest/related-softwares/supy/data-structure/df_state.html?highlight=state_surf#cmdoption-arg-state_surf


    # construct a new state, run the model, and store the state after spin-up
    # expand the state to seven rows, one for each fraction
    df_state_spinup_init=pd.concat([df_state.iloc[[0]]]*7, ignore_index=True,names=['grid'])
    # recover index name
    df_state_spinup_init.index.rename('grid', inplace=True)

    # set the fractions to 100% for each fraction with a 7*7 matrix with 1 on the diagonal
    df_state_spinup_init['sfr_surf'] = np.eye(7)

    # set porosity to 0.5, Issue #78
    df_state_spinup_init["porosity_id"] = 0.5
    df_state_spinup_init["pormax_dec"] = 0.9
    df_state_spinup_init["pormin_dec"] = 0.1

    # construct forcing for spin-up
    # Times in UTC
    end_spinup = site_info['time_analysis_start']
    start_spinup = pd.to_datetime(end_spinup) - timedelta(days=spinup_days)

    # Offset from UTC to Local
    utc_offset = int(site_info['local_utc_offset_hours'])

    # Times in Local Time
    start_spinup_lt = pd.to_datetime(start_spinup) + timedelta(hours=utc_offset)
    end_spinup_lt = pd.to_datetime(end_spinup) + timedelta(hours=utc_offset)

    # Slice forcing
    df_forcing_spinup = df_forcing.loc[start_spinup_lt:end_spinup_lt]

    # Run supy
    df_output_spinup, df_state_spinup = supy.run_supy(
        df_forcing=df_forcing_spinup,
        df_state_init=df_state_spinup_init,
    )

    # retrieve the state after spin-up
    idx_spinup = df_forcing_spinup.index[-1]+df_forcing_spinup.index.freq
    # transfer the spun-up state to the state dataframe for simulation
    for var in ['lai_id', 'soilstore_surf', 'state_surf', 'alb']:
        df_state.loc[:, var] = np.vstack([df_state_spinup.loc[idx_spinup, var].values.diagonal()] * len(df_state))

    # properties specific to deciduous trees
    list_var_dectree = ["porosity_id", "decidcap_id"]
    for var in list_var_dectree:
        df_state.loc[:, var] = df_state_spinup.loc[
            (idx_spinup, 3),
            var,
        ].values[0]

    return df_state

# Routines needed to put Buffer output in Urban-Plumber format
def _get_forcing_output_data(args, site_info, sim_code):

    dict_var_smt = {
        # essential
        "Kup": "SWup",
        "Lup": "LWup",
        "QE": "QEup",
        "QH": "QHup",
        "QF": "Qanth",
        "QS": "dQS",
        # detailed
        "Ts": "AvgSurfT",
        "T2": "TairSurf",
        "AlbBulk": "Albedo",
        "LAI": "LAI",
        "rain": "Rainf",
        "Evap": "Evap",
        "Irr": "Qirrig",
        "RO": "Qs",
        "TotCh": "DelSoilMoist",
        # forcing
        "Kdown": "SWdown",
        "Ldown": "LWdown",
        "Tair_K": "Tair",
        "Qair": "Qair",
        "pres_Pa": "PSurf",
        "U": "Wind",
    }

    # Read forcing, in 300s forcing time step
    output_path = Path('data', site_info['sitename'], 'output', args.run_type)
    df_forcing_raw = pd.read_hdf(output_path / f"df_final_forcing_{sim_code}.h5",
                                 key="df_forcing")

    # Read the model output, in site timestep
    df_output = pd.read_hdf(output_path / f"df_output_{sim_code}.h5",
                            key="df_output")

    # Drop the grid level multi-index
    df_output = df_output.droplevel(0, axis=0)

    # prepare forcing data for submission
    qa = ac(
        "qv",
        RH=df_forcing_raw.RH,
        T=df_forcing_raw.Tair + 273.15,
        p=df_forcing_raw.pres * 100,
    )
    df_forcing_raw = df_forcing_raw.assign(
        Qair=qa,
        Tair_K=df_forcing_raw.Tair + 273.15,
        pres_Pa=df_forcing_raw.pres * 100,
    )

    # Convert to UTC
    utc_offset = int(site_info['local_utc_offset_hours'])
    df_forcing_raw.index = df_forcing_raw.index - timedelta(hours=utc_offset)
    df_output.index = df_output.index - timedelta(hours=utc_offset)

    # Select only forcing from analysis period
    start_analysis = site_info['time_analysis_start']
    end = site_info['time_coverage_end']
    df_forcing_raw = df_forcing_raw.loc[start_analysis:end]
    df_output = df_output.loc[start_analysis:end]

    # Aggregate
    list_var_smt = list(dict_var_smt.keys())
    df_smt_raw = pd.concat([df_output, df_forcing_raw], axis=1)
    df_smt = df_smt_raw[list_var_smt].rename(columns=dict_var_smt)

    # water related variables
    list_var_water = ["Rainf", "Evap", "Qs", "Qirrig"]
    # convert units of water related variables from [mm] to [kg m-2 s-1]
    freq = site_info['timestep_interval_seconds']
    df_smt.loc[:, list_var_water] /= freq

    # temperature related variables
    list_var_temp = ["AvgSurfT", "TairSurf"]
    # convert unit from [degC] to [K]
    df_smt.loc[:, list_var_temp] += 273.15

    df_smt["SWnet"] = df_smt["SWdown"] - df_smt["SWup"]
    df_smt["LWnet"] = df_smt["LWdown"] - df_smt["LWup"]

    # Drop NA, returns data in timestep_interval_seconds
    df_smt = df_smt.dropna()

    return df_smt

def _create_empty_netcdf(site_info, output_path_file):
    """creates empty netcdf dataset complying with Urban-PLUMBER protocol v1.0
    Inputs
    ------
    info (dictionary): script information
    """

    start_analysis = site_info['time_analysis_start']
    end = site_info['time_coverage_end']
    timesteps = len(pd.date_range(
        start_analysis,
        end,
        freq=f"{int(site_info['timestep_interval_seconds'])}s")
    )

    # Some additional information
    site_info["num_soil_layers"] = 1
    missing_float = -9999.0


    # open netcdf files (r = read only, w = write new)
    with nc.Dataset(filename=output_path_file, mode="w", format="NETCDF4") as o:

        # setting coordinate values
        times = [
            t * int(site_info["timestep_interval_seconds"]) for t in range(0, int(timesteps))
        ]
        soil_layers = [i for i in range(1, site_info["num_soil_layers"] + 1)]

        ############ create dimensions ############
        o.createDimension(dimname="time", size=timesteps)
        o.createDimension(dimname="soil_layer", size=site_info["num_soil_layers"])
        o.createDimension(dimname="x", size=1)
        o.createDimension(dimname="y", size=1)

        ############ create coordinates ############
        var = "time"
        o.createVariable(
            var, datatype="i4", dimensions=("time"), fill_value=missing_float
        )
        o.variables[var].long_name = "Time"
        o.variables[var].standard_name = "time"
        o.variables[var].units = "seconds since %s" % site_info["time_analysis_start"]
        o.variables[var].calendar = "standard"
        o.variables[var][:] = times

        var = "soil_layer"
        o.createVariable(
            var, datatype="i4", dimensions=("soil_layer"), fill_value=missing_float
        )
        o.variables[var].long_name = "Soil layer number"
        o.variables[var][:] = soil_layers

        var = "x"
        o.createVariable(var, datatype="i4", dimensions=("x"), fill_value=missing_float)
        o.variables[var].long_name = "x dimension"
        o.variables[var][:] = 1

        var = "y"
        o.createVariable(var, datatype="i4", dimensions=("y"), fill_value=missing_float)
        o.variables[var].long_name = "y dimension"
        o.variables[var][:] = 1

        ################### latidude and longitude ###################

        var = "longitude"
        o.createVariable(
            var, datatype="f8", dimensions=("y", "x"), fill_value=missing_float
        )
        o.variables[var].long_name = "Longitude"
        o.variables[var].standard_name = "longitude"
        o.variables[var].units = "degrees_east"
        o.variables[var][:] = site_info["longitude"]

        var = "latitude"
        o.createVariable(
            var, datatype="f8", dimensions=("y", "x"), fill_value=missing_float
        )
        o.variables[var].long_name = "Latitude"
        o.variables[var].standard_name = "latitude"
        o.variables[var].units = "degrees_north"
        o.variables[var][:] = site_info["latitude"]

        ##########################################################################
        ################### critical energy balance components ###################

        var = "SWnet"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Net shortwave radiation (positive downward)"
        o.variables[var].standard_name = "surface_net_downward_shortwave_flux"
        o.variables[var].units = "W/m2"

        var = "LWnet"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Net longwave radiation (positive downward)"
        o.variables[var].standard_name = "surface_net_downward_longwave_flux"
        o.variables[var].units = "W/m2"

        var = "Qle"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Latent heat flux (positive upward)"
        o.variables[var].standard_name = "surface_upward_latent_heat_flux"
        o.variables[var].units = "W/m2"

        var = "Qh"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Sensible heat flux (positive upward)"
        o.variables[var].standard_name = "surface_upward_sensible_heat_flux"
        o.variables[var].units = "W/m2"

        var = "Qanth"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Anthropogenic heat flux (positive upward)"
        o.variables[
            var
        ].standard_name = (
            "surface_upward_heat_flux_due_to_anthropogenic_energy_consumption"
        )
        o.variables[var].units = "W/m2"

        var = "Qstor"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Net storage heat flux in all materials (increase)"
        o.variables[var].standard_name = "surface_thermal_storage_heat_flux"
        o.variables[var].units = "W/m2"

        var = "SWup"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[
            var
        ].long_name = "Upwelling shortwave radiation flux (positive upward)"
        o.variables[var].standard_name = "surface_upwelling_shortwave_flux_in_air"
        o.variables[var].units = "W/m2"

        var = "LWup"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[
            var
        ].long_name = "Upwelling longwave radiation flux (positive upward)"
        o.variables[var].standard_name = "surface_upwelling_longwave_flux_in_air"
        o.variables[var].units = "W/m2"

        ################### additional energy balance compoenents #################

        var = "Qg"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Ground heat flux (positive downward)"
        o.variables[var].standard_name = "downward_heat_flux_at_ground_level_in_soil"
        o.variables[var].units = "W/m2"

        var = "Qanth_Qh"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[
            var
        ].long_name = "Anthropogenic sensible heat flux (positive upward)"
        o.variables[
            var
        ].standard_name = (
            "surface_upward_sensible_heat_flux_due_to_anthropogenic_energy_consumption"
        )
        o.variables[var].units = "W/m2"

        var = "Qanth_Qle"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Anthropogenic latent heat flux (positive upward)"
        o.variables[
            var
        ].standard_name = (
            "surface_upward_latent_heat_flux_due_to_anthropogenic_energy_consumption"
        )
        o.variables[var].units = "W/m2"

        var = "Qtau"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Momentum flux (positive downward)"
        o.variables[var].standard_name = "magnitude_of_surface_downward_stress"
        o.variables[var].units = "N/m2"

        ##################### general water balance components #####################

        var = "Snowf"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Snowfall rate (positive downward)"
        o.variables[var].standard_name = "snowfall_flux"
        o.variables[var].units = "kg/m2/s"

        var = "Rainf"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Rainfall rate (positive downward)"
        o.variables[var].standard_name = "rainfall_flux"
        o.variables[var].units = "kg/m2/s"

        var = "Evap"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Total evapotranspiration (positive upward)"
        o.variables[var].standard_name = "surface_evapotranspiration"
        o.variables[var].units = "kg/m2/s"

        var = "Qs"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Surface runoff (positive out of gridcell)"
        o.variables[var].standard_name = "surface_runoff_flux"
        o.variables[var].units = "kg/m2/s"

        var = "Qsb"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Subsurface runoff (positive out of gridcell)"
        o.variables[var].standard_name = "subsurface_runoff_flux"
        o.variables[var].units = "kg/m2/s"

        var = "Qsm"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Snowmelt (solid to liquid)"
        o.variables[var].standard_name = "surface_snow_and_ice_melt_flux"
        o.variables[var].units = "kg/m2/s"

        var = "Qfz"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[
            var
        ].long_name = "Re-freezing of water in the snow (liquid to solid)"
        o.variables[var].standard_name = "surface_snow_and_ice_refreezing_flux"
        o.variables[var].units = "kg/m2/s"

        var = "DelSoilMoist"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Change in soil moisture (increase)"
        o.variables[
            var
        ].standard_name = "change_over_time_in_mass_content_of_water_in_soil"
        o.variables[var].units = "kg/m2"

        var = "DelSWE"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Change in snow water equivalent (increase)"
        o.variables[
            var
        ].standard_name = "change_over_time_in_surface_snow_and_ice_amount"
        o.variables[var].units = "kg/m2"

        var = "DelIntercept"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Change in interception storage (increase)"
        o.variables[var].standard_name = "change_over_time_in_canopy_water_amount"
        o.variables[var].units = "kg/m2"

        var = "Qirrig"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[
            var
        ].long_name = "Anthropogenic water flux from irrigation (increase)"
        o.variables[
            var
        ].standard_name = "surface_downward_mass_flux_of_water_due_to_irrigation"
        o.variables[var].units = "kg/m2/s"

        ########################## surface state variables ########################

        var = "SnowT"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Snow surface temperature"
        o.variables[var].standard_name = "surface_snow_skin_temperature"
        o.variables[var].units = "K"
        o.variables[var].subgrid = "snow"

        var = "VegT"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Vegetation canopy temperature"
        o.variables[var].standard_name = "surface_canopy_skin_temperature"
        o.variables[var].units = "K"
        o.variables[var].subgrid = "vegetation"

        var = "BaresoilT"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Temperature of bare soil"
        o.variables[var].standard_name = "surface_ground_skin_temperature"
        o.variables[var].units = "K"
        o.variables[var].subgrid = "baresoil"

        var = "AvgSurfT"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Average surface temperature (skin)"
        o.variables[var].standard_name = "surface_temperature"
        o.variables[var].units = "K"

        var = "RadT"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Surface radiative temperature"
        o.variables[var].standard_name = "surface_radiative_temperature"
        o.variables[var].units = "K"

        var = "Albedo"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Surface albedo"
        o.variables[var].standard_name = "surface_albedo"
        o.variables[var].units = "1"

        var = "SWE"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Snow water equivalent"
        o.variables[var].standard_name = "surface_snow_amount"
        o.variables[var].units = "kg/m2"

        var = "SurfStor"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Surface water storage"
        o.variables[var].standard_name = "surface_water_amount_assuming_no_snow"
        o.variables[var].units = "kg/m2"

        var = "SnowFrac"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Snow covered fraction"
        o.variables[var].standard_name = "surface_snow_area_fraction"
        o.variables[var].units = "1"

        var = "SAlbedo"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Snow albedo"
        o.variables[var].standard_name = "snow_and_ice_albedo"
        o.variables[var].units = "1"
        o.variables[var].subgrid = "snow"

        var = "CAlbedo"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Vegetation canopy albedo"
        o.variables[var].standard_name = "canopy_albedo"
        o.variables[var].units = "1"
        o.variables[var].subgrid = "vegetation"

        var = "UAlbedo"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Urban canopy albedo"
        o.variables[var].standard_name = "urban_albedo"
        o.variables[var].units = "1"
        o.variables[var].subgrid = "urban"

        var = "LAI"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Leaf area index"
        o.variables[var].standard_name = "leaf_area_index"
        o.variables[var].units = "1"
        o.variables[var].subgrid = "vegetation"

        var = "RoofSurfT"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Roof surface temperature (skin)"
        o.variables[var].standard_name = "surface_roof_skin_temperature"
        o.variables[var].units = "K"
        o.variables[var].subgrid = "roof"

        var = "WallSurfT"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Wall surface temperature (skin)"
        o.variables[var].standard_name = "surface_wall_skin_temperature"
        o.variables[var].units = "K"
        o.variables[var].subgrid = "wall"

        var = "RoadSurfT"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Road surface temperature (skin)"
        o.variables[var].standard_name = "surface_road_skin_temperature"
        o.variables[var].units = "K"
        o.variables[var].subgrid = "road"

        var = "TairSurf"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Near surface air temperature (2m)"
        o.variables[var].standard_name = "air_temperature_near_surface"
        o.variables[var].units = "K"

        var = "TairCanyon"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Air temperature in street canyon (bulk)"
        o.variables[var].standard_name = "air_temperature_in_street_canyon"
        o.variables[var].units = "K"
        o.variables[var].subgrid = "canyon"

        var = "TairBuilding"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Air temperature in buildings (bulk)"
        o.variables[var].standard_name = "air_temperature_in_buildings"
        o.variables[var].units = "K"
        o.variables[var].subgrid = "building"

        ######################## Sub-surface state variables ######################

        var = "SoilMoist"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "soil_layer", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Average layer soil moisture"
        o.variables[var].standard_name = "moisture_content_of_soil_layer"
        o.variables[var].units = "kg/m2"

        var = "SoilTemp"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "soil_layer", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Average layer soil temperature"
        o.variables[var].standard_name = "soil_temperature"
        o.variables[var].units = "K"

        ########################## Evaporation components #########################

        var = "TVeg"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Vegetation transpiration"
        o.variables[var].standard_name = "transpiration_flux"
        o.variables[var].units = "kg/m2/s"
        o.variables[var].subgrid = "vegetation"

        var = "ESoil"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Bare soil evaporation"
        o.variables[var].standard_name = "liquid_water_evaporation_flux_from_soil"
        o.variables[var].units = "kg/m2/s"
        o.variables[var].subgrid = "baresoil"

        var = "RootMoist"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Root zone soil moisture"
        o.variables[
            var
        ].standard_name = "mass_content_of_water_in_soil_defined_by_root_depth"
        o.variables[var].units = "kg/m2"

        var = "SoilWet"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Total soil wetness"
        o.variables[
            var
        ].standard_name = "relative_soil_moisture_content_above_wilting_point"
        o.variables[var].units = "1"

        var = "ACond"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Aerodynamic conductance"
        o.variables[var].standard_name = "inverse_aerodynamic_resistance"
        o.variables[var].units = "m/s"

        ########################## forcing data variables #########################

        var = "SWdown"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[
            var
        ].long_name = "Downward shortwave radiation at measurement height"
        o.variables[var].standard_name = "surface_downwelling_shortwave_flux_in_air"
        o.variables[var].units = "W/m2"

        var = "LWdown"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Downward longwave radiation at measurement height"
        o.variables[var].standard_name = "surface_downwelling_longwave_flux_in_air"
        o.variables[var].units = "W/m2"

        var = "Tair"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Air temperature at measurement height"
        o.variables[var].standard_name = "air_temperature"
        o.variables[var].units = "K"

        var = "Qair"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Specific humidity at measurement height"
        o.variables[var].standard_name = "surface_specific_humidity"
        o.variables[var].units = "1"

        var = "PSurf"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Air pressure at measurement height"
        o.variables[var].standard_name = "surface_air_pressure"
        o.variables[var].units = "Pa"

        var = "Wind"
        o.createVariable(
            var,
            datatype="f8",
            dimensions=("time", "y", "x"),
            fill_value=missing_float,
            zlib=True,
        )
        o.variables[var].long_name = "Wind speed at measurement height"
        o.variables[var].standard_name = "wind_speed"
        o.variables[var].units = "m/s"

    return
def _set_netcdf_data(site_info, data, fname, sim_code):

    """
    Write model data values into existing netCDF file.
    This function sets a small number of variables as an example.
    Please include all available model output.
    Note subsurface state variables are two dimensional {time, soil_layer}.
    Inputs
    ------
    site_info (dictionary): script information
    data (dataframe): model data
    """

    timestep_interval_seconds = int(site_info['timestep_interval_seconds'])
    start_analysis = site_info['time_analysis_start']
    end = site_info['time_coverage_end']
    timesteps = len(pd.date_range(
        start_analysis,
        end,
        freq=f"{timestep_interval_seconds}s")
    )

    # Some additional information
    missing_float = -9999.0

    # General info, set in separate dict
    info = {}
    # site name
    info["sitename"] = f"{site_info['sitename']}"
    # model name
    info["model"] = "SUEUWS/SUPY"
    # configuration
    info["cfg"] = sim_code
    # list number of soil layers in model
    info["num_soil_layers"] = 1

    # other meta-info
    info["institution"] = "Bochum Urban Climate Lab, Ruhr-University Bochum, Germany"
    info["first_contact"] = "Matthias Demuzere, matthias.demuzere@rub.de"
    info["second_contact"] = "Ting Sun, ting.sun@ucl.ac.uk"
    info["ref"] = "Jarvi et al. (2011, JoH); Ward et al. (2016, UrbClim)"
    info["repo"] = "Per request"
    info[
        "site_exp"
    ] = "extensively used in several UK, North American and Chinese cities"
    info["additional_data"] = "No"
    info["note"] = "NA"

    # define empty numpy arrays for missing data
    no_data_1D = np.full([timesteps], missing_float)
    no_data_2D = np.full([timesteps, info["num_soil_layers"]], missing_float)

    # open netcdf files (r = read only, r+ = append existing)
    with nc.Dataset(filename=fname, mode="r+", format="NETCDF4") as o:
        # set metadata
        o.title = f"{info['model']} output for SUPY-LCZ work, in Urban-PLUMBER format"
        o.site = info["sitename"]
        o.experiment = info["cfg"]
        o.institution = info["institution"]
        o.primary_contact = info["first_contact"]
        o.secondary_contact = info["second_contact"]
        o.model = info["model"]
        o.source = info["model"]
        o.references = info["ref"]
        o.repository = info["repo"]
        o.site_experience = info["site_exp"]
        o.additional_data = info["additional_data"]
        o.comment = info["note"]

        o.history = "Created with the sypy-lcz runner at %s" % (pd.Timestamp.now())

        # Critical energy balance components
        o.variables["SWnet"][:] = data["SWnet"].values  # Net shortwave radiation (downward)
        o.variables["LWnet"][:] = data["LWnet"].values  # Net longwave radiation (downward)
        o.variables["Qle"][:] = data["QEup"].values  # Latent heat flux (upward)
        o.variables["Qh"][:] = data["QHup"].values  # Sensible heat flux (upward)
        o.variables["Qanth"][:] = data["Qanth"].values  # Anthropogenic heat flux (upward)
        o.variables["Qstor"][:] = data["dQS"].values  # Net storage heat flux in all materials (increase)
        o.variables["SWup"][:] = data["SWup"].values  # Upwelling shortwave radiation flux (upward)
        o.variables["LWup"][:] = data["LWup"].values  # Upwelling longwave radiation flux (upward)

        # Additional energy balance components
        o.variables["Qg"][:] = data["dQS"].values  # Ground heat flux (downward)
        o.variables["Qanth_Qh"][:] = no_data_1D  # Anthropogenic sensible heat flux (upward)
        o.variables["Qanth_Qle"][:] = no_data_1D  # Anthropogenic latent heat flux (upward)
        o.variables["Qtau"][:] = no_data_1D  # Momentum flux (downward)

        # General water balance components
        o.variables["Snowf"][:] = no_data_1D  # Snowfall rate (downward)
        o.variables["Rainf"][:] = data["Rainf"].values  # Rainfall rate (downward)
        o.variables["Evap"][:] = data["Evap"].values  # Total evapotranspiration (upward)
        o.variables["Qs"][:] = data["Qs"].values  # Surface runoff (out of gridcell)
        o.variables["Qsb"][:] = no_data_1D  # Subsurface runoff (out of gridcell)
        o.variables["Qsm"][:] = no_data_1D  # Snowmelt (solid to liquid)
        o.variables["Qfz"][:] = no_data_1D  # Re-freezing of water in the snow (liquid to solid)
        o.variables["DelSoilMoist"][:] = data["DelSoilMoist"].values  # Change in soil moisture (increase)
        o.variables["DelSWE"][:] = no_data_1D  # Change in snow water equivalent (increase)
        o.variables["DelIntercept"][:] = no_data_1D  # Change in interception storage (increase)
        o.variables["Qirrig"][:] = data["Qirrig"].values  # Anthropogenic water flux from irrigation (increase)

        # Surface state variables
        o.variables["SnowT"][:] = no_data_1D  # Snow surface temperature
        o.variables["VegT"][:] = no_data_1D  # Vegetation canopy temperature
        o.variables["BaresoilT"][:] = no_data_1D  # Temperature of bare soil (skin)
        o.variables["AvgSurfT"][:] = data["AvgSurfT"].values  # Average surface temperature (skin)
        o.variables["RadT"][:] = no_data_1D  # Surface radiative temperature
        o.variables["Albedo"][:] = data["Albedo"].values  # Surface albedo
        o.variables["SWE"][:] = no_data_1D  # Snow water equivalent
        o.variables["SurfStor"][:] = no_data_1D  # Surface water storage
        o.variables["SnowFrac"][:] = no_data_1D  # Snow covered fraction
        o.variables["SAlbedo"][:] = no_data_1D  # Snow albedo
        o.variables["CAlbedo"][:] = no_data_1D  # Vegetation canopy albedo
        o.variables["UAlbedo"][:] = no_data_1D  # Urban canopy albedo
        o.variables["LAI"][:] = data["LAI"].values  # Leaf area index
        o.variables["RoofSurfT"][:] = no_data_1D  # Roof surface temperature (skin)
        o.variables["WallSurfT"][:] = no_data_1D  # Wall surface temperature (skin)
        o.variables["RoadSurfT"][:] = no_data_1D  # Road surface temperature (skin)
        o.variables["TairSurf"][:] = data["TairSurf"].values  # Near surface air temperature (2m)
        o.variables["TairCanyon"][:] = no_data_1D  # Air temperature in street canyon (bulk)
        o.variables["TairBuilding"][:] = no_data_1D  # Air temperature in buildings (bulk)

        # Sub-surface state variables **** TWO DIMENSIONAL ****
        # ---shape: [timesteps, num_soil_layers]
        # o.variables["SoilMoist"][:, :] = no_data_2D  # Average layer soil moisture
        deltaSoilMoist = data["DelSoilMoist"].values
        o.variables["SoilMoist"][:, :] = np.reshape(deltaSoilMoist / timestep_interval_seconds,
                                                    (len(deltaSoilMoist), 1))  # Average layer soil moisture
        o.variables["SoilTemp"][:, :] = no_data_2D  # Average layer soil temperature

        # Evaporation components
        o.variables["TVeg"][:] = no_data_1D  # Vegetation transpiration
        o.variables["ESoil"][:] = no_data_1D  # Bare soil evaporation
        o.variables["RootMoist"][:] = no_data_1D  # Root zone soil moisture
        o.variables["SoilWet"][:] = no_data_1D  # Total soil wetness
        o.variables["ACond"][:] = no_data_1D  # Aerodynamic conductance
        # Forcing data (at forcing height)
        o.variables["SWdown"][:] = data["SWdown"].values  # Downward shortwave radiation
        o.variables["LWdown"][:] = data["LWdown"].values  # Downward longwave radiation
        o.variables["Tair"][:] = data["Tair"].values  # Air temperature
        o.variables["Qair"][:] = data["Qair"].values  # Specific humidity
        o.variables["PSurf"][:] = data["PSurf"].values  # Air pressure
        o.variables["Wind"][:] = data["Wind"].values  # Wind speed

    return

def store_output_h5(df_output, site_info, suews_output_file, freq_out):

    # only take the data from time_analysis_start:
    # simulation in LT, time_analysis_start in UTC!!
    utc_offset = int(site_info['local_utc_offset_hours'])
    start_analysis = site_info['time_analysis_start']
    start_analysis_lt = pd.to_datetime(start_analysis) \
                        + timedelta(hours=utc_offset)

    df_output_suews = df_output['SUEWS']
    df_output_suews = df_output_suews.swaplevel(0, 1)

    # datetime index needs to be sorted, otherwise slicing does not work
    df_output_suews.sort_index(inplace=True)

    # Select period of interest
    df_output_suews_analysis = df_output_suews.\
        loc[start_analysis_lt:datetime.utcnow().isoformat()]

    # # Resample to chosen output interval, sum for precip, mean for other vars
    # df_output_suews_rsmp = (
    #     df_output_suews_analysis.unstack('grid').resample(f'{freq_out}T').mean()
    # )
    # ser_rainfall_rsmp = (
    #     df_output_suews_analysis.unstack('grid').Rain.resample(f'{freq_out}T').sum()
    # )

    # Addressing the averaging, using a time ending definition
    df_output_suews_rsmp = (
        df_output_suews_analysis.unstack('grid').resample(
            f'{freq_out}T', closed='right', label='right').mean()
    )
    ser_rainfall_rsmp = (
        df_output_suews_analysis.unstack('grid').Rain.resample(
            f'{freq_out}T', closed='right', label='right').sum()
    )

    df_output_suews_rsmp = df_output_suews_rsmp.assign(Rain=ser_rainfall_rsmp)

    # recover `grid` into index
    df_output_suews_rsmp = df_output_suews_rsmp.stack().swaplevel()

    # show the size of reduced output df
    df_output_suews_rsmp.info(verbose=False, memory_usage='deep')

    # Store selected output
    df_output_suews_rsmp.to_hdf(
        suews_output_file,
        key=f"df_output",
        complevel=9,
        complib="blosc:lz4hc",
    )

    return

def store_output_nc(args, site_info, sim_code, suews_output_file_up):

    # Get the .h5 forcing and output data and reduce to what is needed
    # This data is converted back to UTC
    data = _get_forcing_output_data(args, site_info, sim_code)

    # Initialize netcdf file to store data in
    _create_empty_netcdf(site_info, suews_output_file_up)

    # Store all data into netcdf file
    _set_netcdf_data(site_info, data, suews_output_file_up, sim_code)

    return


## OLD - no longer used -
# def _get_deciduous_tree_ratio(
#         site_info: dict[str, Any],
#         roi: Grid | Buffer,
# ) -> float:
#
#     '''
#     Helper function to get fraction of tree types, per LCZ class in ROI.
#
#     Available forest types from Copernicus land cover layer
#     0	Unknown
#     1	Evergreen needle leaf
#     2	Evergreen broad leaf
#     3	Deciduous needle leaf
#     4	Deciduous broad leaf
#     5	Mix of forest types
#
#     Output: ratio of deciduous trees per LCZ class
#     '''
#
#     # LCZ map
#     lcz_file = Path('data', site_info['sitename'], 'input', 'download.LCZ_Filter.tif')
#     lcz = rxr.open_rasterio(lcz_file).rio.clip(roi.gdf.geometry, all_touched=True)
#
#     # Tree type
#     ft_file = Path('data', site_info['sitename'], 'input', '2019.forest_type.tif')
#     ft = rxr.open_rasterio(ft_file)[0,:,:].rio.clip(roi.gdf.geometry, all_touched=True)
#
#
#
#     # Mask values
#     ft_m = xr.where(ft<0, np.nan, ft)
#
#     # Count unqiue values
#     ft_list = ft_m.values.tolist()
#     ft_values, ft_counts = np.unique(ft_list, return_counts=True)
#     ft_values, ft_counts
#
#     # Check if ROI contains any tree pixels
#     tree_present = any(x in [1,2,3,4,5] for x in ft_values)
#
#     if tree_present:
#
#         tree_pixels = 0
#         deciduous_cnt = 0
#         evergeen_cnt = 0
#
#         # Get the relevent tree info
#         for i_x, i in enumerate(ft_values):
#
#             # Count all tree pixels
#             if i in [1,2,3,4,5]:
#                 tree_pixels += ft_counts[i_x]
#
#             # Count deciduous, half of mixed put into deciduous
#             if i in [3, 4, 5]:
#                 if i != 5:
#                     deciduous_cnt += ft_counts[i_x]
#                 else:
#                     deciduous_cnt += ft_counts[i_x]/2
#
#             # Count evergreen, half of mixed put into evergreen
#             if i in [1, 2, 5]:
#                 if i != 5:
#                     evergeen_cnt += ft_counts[i_x]
#                 else:
#                     evergeen_cnt += ft_counts[i_x]/2
#
#         # Sanity check
#         if evergeen_cnt + deciduous_cnt == tree_pixels:
#             print('all tree pixels counted for.')
#
#         # deciduous ratio
#         ratio_deciduous = np.round(deciduous_cnt / tree_pixels, 2)
#
#     else:
#         ratio_deciduous = np.nan
#
#     return ratio_deciduous
#
#
# def _tree_height_stats(site_info) -> dict[str, float]:
#
#     th_file = Path('data', site_info['sitename'], 'input', '2019.GCFH.tif')
#
#     # Open file and mask non-treed pixels
#     th = rxr.open_rasterio(th_file)[0, :, :]
#     th = th.where(th > 0)
#
#     # Get mean, max and std of tree height
#     if len(th > 0) > 0:
#         th_stats = {
#             'th_mean' : float(th.mean()),
#             'th_max' : float(th.max()),
#             'th_std' : float(th.std())
#         }
#
#     else:
#         th_stats = np.nan
#
#     return th_stats














