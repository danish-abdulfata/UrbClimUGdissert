# -*- coding: utf-8 -*-
"""
Created on Thu Jul  3 18:37:05 2025

@author: Danish
"""

import pandas as pd
import os
import numpy as np
import xarray as xr
from pathlib import Path

import geopandas as gpd


os.chdir(r"C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global")

# use the same names as set in run_split_models

output_file = './data/consolidated_outputs/'
site_prefix = "GreaterKL-2017_Y1_M2sp_3sf_R1"

data_file = Path(output_file, site_prefix + '_consolidated.nc')
data_file_attr = Path(output_file, site_prefix + 'surffrac_consolidated.csv')

data = pd.read_hdf(data_file)
data_attr = pd.read_csv(data_file_attr)

import matplotlib.pyplot as plt



