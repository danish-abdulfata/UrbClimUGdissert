import matplotlib.pyplot as plt
import supy as sp
import pandas as pd
import numpy as np
from pathlib import Path

df_output = pd.read_hdf(r"C:\Users\Danish\Documents\lcz-supy-global-data\AU-SurreyHills\output\buffer\df_output_era5l_MF_lczu_LC.h5")
df_state_final = pd.read_pickle(r"C:\Users\Danish\Documents\lcz-supy-global-data\AU-SurreyHills\output\buffer\df_state_final_sMF_lczu_LC.pkl")

list_path_save = sp.save_supy(df_output, df_state_final)
for file_out in list_path_save:
    print(file_out.name)