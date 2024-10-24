from runner.utils import gen_era5land_forcing
from runner.utils import format_era5land_forcing
from pathlib import Path
import pandas as pd
import time

def get_city_from_site_list(city: str) -> pd.Series:
    site_list = pd.read_csv(
        '/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/resources/sitelist_urbanplumber.csv')
    # this should always only be a one row df!
    return site_list[site_list['sitename'] == city].iloc[0]

cities  = [
    "AU-Preston",
    "AU-SurreyHills",
    "CA-Sunset",
    "FI-Kumpula",
    "FI-Torni",
    "FR-Capitole",
    "GR-HECKOR",
    "JP-Yoyogi",
    "KR-Jungnang",
    "KR-Ochang",
    "MX-Escandon",
    "NL-Amsterdam",
    "PL-Lipowa",
    "PL-Narutowicza",
    "SG-TelokKurau06",
    "UK-KingsCollege",
    "UK-Swindon",
    "US-Baltimore",
    "US-Minneapolis1",
    "US-Minneapolis2",
    "US-WestPhoenix",
]

for city in cities:

    start = time.time()

    print(city)
    site_info = get_city_from_site_list(city)

    # Set the directoy, read the raw files
    fndir = "/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/data"
    dir_save = Path(fndir, site_info['sitename'], 'input', 'era5land')
    dir_save.mkdir(parents=True, exist_ok=True)

    print("    -- Downloading ERA5-LAND forcing. This may take some time ...")
    gen_era5land_forcing(site_info, dir_save)

    print("    -- Make the ERA5-LAND forcing readable by SUPY")
    format_era5land_forcing(site_info, dir_save)

    # Check how long it takes ...
    end = time.time()

    # Subtract Start Time from The End Time
    total_time = end - start
    print("\n" + str(total_time))
    print("-----------------------")