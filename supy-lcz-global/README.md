# supy-lcz-global

## Environments

### Working with `micromamba` (preferred):
[micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html#micromamba) is a lightweight version of conda with much faster performance and thus recommended over conda.
You can [download Mambaforge (GitHub page)](https://github.com/conda-forge/miniforge#mambaforge) for Windows, macOS and Linux.

Then set up the required environment in your terminal as follows:
```bash
> micromamba create -f env.yml # set up environment
> micromamba activate supy_lcz # activate environment
```


### Working with `conda`

_note: conda can be very slow. Therefore micromamba is recommended._

```bash
> conda create -n supy_lcz_py39 python=3.9
> .conda activate supy_lcz_py39
```

I installed all packages as follows (separately, in this order):
```bash
> conda install geopandas georasters earthengine-api netCDF4 rioxarray xarray pytables shapely opencv
```
I added the last two, as I got an error when installing supy for the first time:
`ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts. pointpats 2.2.0 requires opencv-contrib-python>=4.2.0, which is not installed.
`

and then at the end supy:
```bash
> pip install -U supy
```

when ready, store environment with `conda env export > environment.yml`.
This environment can now be installed with:
```bash
> conda env create -f environment.yml
```

### Working with `venv`

_Note to adjust the gdal version, in line with the version available on your system._
```bash
> python3.9 -m venv up_py39
> . up_py39/bin/activate
> pip install -r requirements-minimal.txt
```

## running the model

You can run the model for a specific city using this command (expecting being present in `./data`)

```bash
python -m runner.runner AU-Preston --run-type buffer
```

Other options can be specified:

```console
usage: runner.py [-h] [city] [--run-type {buffer,grid}] [--grid-size GRID_SIZE] [--grid-boxes GRID_BOXES]
[--metforc-src {obs, era5}] [--urbdesc-src {up_baseline, up_detailed, lcz_default, lcz_updated}]
[--initialize-only] [--do-spinup] [--sitelist]

positional arguments:
  city

options:
  -h, --help            show this help message and exit
  --run-type {buffer,grid}
  --grid-size GRID_SIZE
  --grid-boxes GRID_BOXES
  --metforc-src {obs, era5land}
  --urbdesc-src {up_detailed, lcz_updated}
  --download-era5
  --initialize-only
  --do-spinup
  --sitelist
[tmp](tmp)
```

Notes:

* `--grid-size`: horizontal resolution of grid box, in meters (only relevant for `--run-type grid`)
* `--grid-boxes`: number of grid cells in x and y direction (same for both, only relevant for `--run-type grid`)
* `--metforc-src` refers to the meteorological forcing. This can be either:
  * `obs`: observed at the flux tower, and gap-filled, as used in [Urban Plumber](https://essd.copernicus.org/articles/14/5157/2022/essd-14-5157-2022.pdf),
  * `era5`: the raw ERA5 forcing without any observations or gap-filling  - REMOVED,
  * `era5land`: the raw ERA5Land hourly forcing, retrieved from [Google Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY)
* `--urbdesc-src` decides which urban description to use:
  * `up_baseline`: baseline site description as used in Urban Plumber. See more information [here (Section 6.3, Table 2)](https://urban-plumber.github.io/static/Urban-PLUMBER_protocol_v1.pdf) - REMOVED
  * `up_detailed`: detailed site description as used in Urban Plumber. See more information [here (Section 6.3, Table 2)](https://urban-plumber.github.io/static/Urban-PLUMBER_protocol_v1.pdf)
  * `lcz_default`: using the default conversion table, as provided in `resources/`  - REMOVED
  * `lcz_updated`: update the conversion table for a number of parameters, using different global datasets:
    * Natural (pervious) land cover fractions: The loop-up tables by Stewart and Oke (2012) do not provide details on the pervious fraction of the surface. Therefore, the 10m [ESA WorldCover map](https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v100?hl=en#description) is used to identify the fractions of trees, grass, bare soil and water.
    * Tree type (deciduous / evergreen): based on the 100m forest type data from [the Copernicus land cover layer v3](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global)
    * Mean vegetation height (meters, refers to trees): taken from the 30m [GEDI-based global forest canopy height](https://doi.org/10.1016/j.rse.2020.112165)
* `--download-era5`: if set, the ERA5 or ERA5LAND data is downloaded from CDS or GEE respectively.
* `--initialize-only`: if set, only the initialisation is done, and supy is **not** run.
* `--do-spinup`: for non-UP sites, only for `run-type = grid`. If set, 2 years of spin-up are done. For a buffer, spin-up is done by default (also 2 years)
* `--sitelist`: filename with custom site list information, in same folder as default `sitelist_urbanplumber.csv`


## Including the data

Since the data was too big to be stored on GitHub, it was moved to [this data folder](https://geo-cloud.geographie.ruhr-uni-bochum.de/index.php/s/WyXcKiRzL8tFimX) on RUB's Geo-Cloud. The password to access the folder: `g75T2r7ks9`.

1. Either download the data or setup a Nextcloud-sync
1. While in the repo run the following command to create a symbolic link to have the data folder
   available as `./data` in the repositories root. It works best if you use absolute paths.
   ```bash
   ln --symbolic /home/<user>/<some-other-folders>/lcz-supy-global-data /home/<user>/<some-other-folders>/supy-lcz-global/data
   ```
1. You now should have a symbolic link for `./data`
   ```console
   kittnjdr@ububox:~/workspace/supy-lcz-global$ ls -l
   total 32
   lrwxrwxrwx 1 kittnjdr kittnjdr   40 Nov 22 13:51 data -> /home/demuzmp4/Nextcloud/data/supy-lcz-global-data
   -rw-rw-r-- 1 kittnjdr kittnjdr  667 Nov 22 13:55 README.md
   -rw-rw-r-- 1 kittnjdr kittnjdr    7 Okt 25 18:32 requirements-dev-minimal.txt
   -rw-rw-r-- 1 kittnjdr kittnjdr  128 Nov 22 13:46 requirements-minimal.txt
   drwxrwxr-x 2 kittnjdr kittnjdr 4096 Okt 25 17:49 resources
   drwxrwxr-x 3 kittnjdr kittnjdr 4096 Okt 25 18:10 runner
   drwxrwxr-x 2 kittnjdr kittnjdr 4096 Okt 25 17:48 scripts
   drwxrwxr-x 2 kittnjdr kittnjdr 4096 Okt 25 17:48 tests
   drwxrwxr-x 6 kittnjdr kittnjdr 4096 Okt 25 18:28 venv
   ```

## Processing

### Get initial df_state for all simulation types

```bash
python helper_scripts/batch_get_df_state.py 2>&1 | tee batch_get_df_state.log
```

### Plot the fractions from df_state, for all simulations

```bash
python visualize/plt_df_state_fractions.py
```

### Plot the changed state variables, per site, as a table

```bash
python visualize/plt_df_state_table.py
```

### Plot the forcing, split for spin-up and analysis period, for all experiments

```bash
# some deviations because of internal forcing interpolation in SUEWS?
python visualize/check_output_forcing.py
```

### Plot the modelled fluxes, against the observations, for all experiments

```bash
python visualize/check_output_fluxes.py
```
