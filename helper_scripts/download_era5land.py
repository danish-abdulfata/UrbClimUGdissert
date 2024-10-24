import os
from pathlib import Path
import ee
import pandas as pd
import time
from datetime import timedelta

start = time.time()

ee.Initialize()


# Required variables:
# * U: u_component_of_wind_10m, v_component_of_wind_10m [m/s]
# * Press: surface_pressure [Pa]
# * Td: dewpoint_temperature_2m [K],  Combined with temperature and pressure, it can be used to calculate the relative humidity
# * Tair: temperature_2m [K]
# * RH: Get from Tair, Td and Press
# * Rain: total_precipitation [m, accumulated from the beginning of the forecast time to the end of the forecast step.]
# * Kdown: surface_solar_radiation_downwards [J/m2]
# * Ldown: surface_thermal_radiation_downwards [J/m2]


# SITE = "AU-Preston"
# aoi = ee.Geometry.Point([145.0145, -37.7306])
# startdate = '2003-08-12'
# #enddate =  '2003-08-13'; # 1 day takes ~ few seconds - size 3.6 kb
# #enddate =  '2003-09-12'; # 1 month takes ~ 25 seconds - size 111.5 kb
# enddate =  '2004-11-28'; # analysis period (16 months) takes ~ 240 seconds - size 1.7 mb

# SITE = "US-Baltimore"
# aoi = ee.Geometry.Point([-76.5215, 39.4128])
# startdate = '2002-01-01'
# enddate =  '2007-01-01'

def _era5land_store_timeseries_to_df(ic, startdate, enddate, aoi, dir_save):

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
        .filterDate(ee.Date(startdate).advance(-2, 'day'),ee.Date(enddate).advance(2, 'day')) \
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
            scale=imgRep.projection().nominalScale(),
            crs=imgRep.projection().crs()
            ).map(set_properties)

        return ee.FeatureCollection(col)

    results = era5_land.map(_era5land_get_timeseries).flatten()
    # print(results.getInfo())

    # CHECK: https://kaflekrishna.com.np/blog-detail/extraction-raster-values-point-samples-google-earth-engine-gee/
    nested_list = results.reduceColumns(ee.Reducer.toList(len(variables_export)), variables_export).values().get(0)
    data = nested_list.getInfo()

    # Convert to pandas dataframe
    df = pd.DataFrame(data, columns=variables_export)

    # Save to drive
    OFILE = os.path.join(
        dir_save,
        f"ERA5LAND_{startdate}-{enddate}.txt",
    )
    df.to_csv(OFILE, index=False)


def _era5land_download_forcing(site_info, dir_save):

    startdate = pd.to_datetime(site_info['time_analysis_start']).date() + timedelta(days=-2)
    enddate = pd.to_datetime(site_info['time_coverage_end']).date() + timedelta(days=2)
    aoi = ee.Geometry.Point([site_info['longitude'], site_info['latitude']])

    # Input data: ERA5-Land hourly
    # https:#developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY
    ic = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY")

    # If time span is too long, it will result in a computation time out.
    # So the request needs to be split in chunks, e.g. per ~ year.
    # Check length of the request in days
    time_span_days = (enddate - startdate).days

    if time_span_days > 365:

        # Initialize chunk start- and enddates
        startdate_chunk = startdate
        enddate_chunk = startdate_chunk.replace(
            year=startdate_chunk.year+1, month=1, day=1
        )

        while startdate_chunk < enddate:

            # Set end date to final analysis time, for last chunk
            if enddate_chunk > enddate:
                # Need to add one day to enddate, as last day is otherwise missing
                enddate_chunk = enddate + timedelta(days=1)

            # Get the timeseries for this year
            print(startdate_chunk.strftime('%Y-%m-%d'), enddate_chunk.strftime('%Y-%m-%d'))
            _era5land_store_timeseries_to_df(
                ic=ic,
                startdate=startdate_chunk.strftime('%Y-%m-%d'),
                enddate=enddate_chunk.strftime('%Y-%m-%d'),
                aoi=aoi,
                dir_save=dir_save,
            )

            # Reset startdate to next chunck
            startdate_chunk = enddate_chunk
            enddate_chunk = startdate_chunk.replace(
                year=startdate_chunk.year+1, month=1, day=1
            )

    else:
        # Need to add one day to enddate, as last day is otherwise missing
        _era5land_store_timeseries_to_df(
            ic=ic,
            startdate=startdate.strftime('%Y-%m-%d'),
            enddate=enddate.strftime('%Y-%m-%d'),
            aoi=aoi,
            dir_save=dir_save,
        )

city = "AU-Preston"
def get_city_from_site_list(city: str) -> pd.Series:
    site_list = pd.read_csv(
        '/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/resources/sitelist_urbanplumber.csv')
    # this should always only be a one row df!
    return site_list[site_list['sitename'] == city].iloc[0]
site_info = get_city_from_site_list(city)

# Set the directoy
fndir = "/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/data"
dir_save = Path(fndir, city, 'input', 'era5land')
dir_save.mkdir(parents=True, exist_ok=True)

# Download the forcing
_era5land_download_forcing(site_info, dir_save)

# Check how long it takes ...
end = time.time()

#Subtract Start Time from The End Time
total_time = end - start
print("\n"+ str(total_time))

