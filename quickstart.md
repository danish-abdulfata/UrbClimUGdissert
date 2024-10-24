# Quick Start Guide

Written by [Matthias Demuzere](https://github.com/matthiasdemuzere) and edited by [Ting Sun](https://github.com/matthiasdemuzere)

The explanation below is valid for unknown sites, meaning that they are not part of [Urban-Plumber](https://urban-plumber.github.io/sites).


## Installation and requirements

- Check [README](./README.md#working-with-micromamba-preferred), so far I have been using [micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html), currently with the latest development version of [supy](https://pypi.org/project/supy/#history).
- Make sure to have an account on Google's Earth Engine, and have their [api installed and authenticated](https://developers.google.com/earth-engine/guides/python_install).
- a data folder needs to be available within the script directory. Either physically there, or via a symbolic link.

## FOR A SINGLE-POINT (BUFFER) EXPERIMENT

### Simulating a buffer

See explanation of the arguments in [README](./README.md).

```python
python -m runner.runner BE-Ghent --run-type buffer --metforc-src era5land --urbdesc-src lcz_updated --sitelist sitelist_custom --download-era5 --do-spinup
```

### Notes
- define your site(s) in `resources/sitelist_custom.csv`. I believe most fields in this file are self-explanatory, except maybe:
   - `surface_cover_radius`: footprint you like to model. In UP e.g., this is either 500 or 1000 meter.
   - `time_analysis_start`: startdate of the period you are interested in
   - `time_coverage_end`: end time of simulation
   - `timestep_interval_seconds`: the output frequency you want to have.
- since sites are unknown, meteoforcing and land cover description data should be universal, hence `--metforc-src era5land` and `--urbdesc-src lcz_updated`
- `sitelist` points to the sitelist_custom.csv file, where you have listed and described your site(s) of interest.
- Setting `--download-era5` will download ERA5 data. If not set, the system assumes the required files are already available.
- Setting `--do-spinup` will introduce a spin-up of 2 years prior to the `time_analysis_start` date.

### Sample Results

Running the above command should provide you with the following output in `.data/BE-Ghent/`:

![image](https://github.com/matthiasdemuzere/supy-lcz-global/assets/6926916/57196fe2-86c2-4976-9fbb-5b800686a241)


## FOR A GRID EXPERIMENT


Very similar as the above, with some changes in the command:

```python
python -m runner.runner CH-Shanghai --run-type grid --grid-size 300 --grid-boxes 3 --metforc-src era5land --urbdesc-src lcz_updated --sitelist sitelist_custom --download-era5
```

Here:
- `--run-type` should be set to `grid `
- `--grid-size` is resolution of grid cell in meters
- `--grid-boxes` is number of grid boxes in both x and y direction

### Sample Results

Same structure as for the buffer, but this time under the _grid_ subfolders:

![image](https://github.com/matthiasdemuzere/supy-lcz-global/assets/6926916/2c6331d3-c654-41fb-a902-d0c0370ee828)


### Notes
- adding the `--do-spinup` argument would also invoke a 2-year spinup cycle. Yet there are still some issues with this, see #75 , #78
- In the example above, I have used a very low number of grid-boxes, as I was trying this on my local machine that is completely full and low on memory. Larger domains are of course possible.
- That said, the GEE api has limits, which I have not tested completely yet. So far,  a max domain extent of ~21 kilometers seems to work (eg.` --grid-size 300 --grid-boxes 70`). See also #71
