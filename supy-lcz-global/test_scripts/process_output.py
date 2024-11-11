import os
os.environ['USE_PYGEOS'] = '0'
import supy as sp
import pandas as pd
import numpy as np
from pathlib import Path

sh_suews_output = r'C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global\data\CH-Shanghai\output\grid\df_output_uMF_uLCu.h5'

sh_state_final = r'C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global\data\CH-Shanghai\output\grid\df_final_forcing_uMF_uLCu.h5'

df_sh_output = pd.read_hdf(sh_suews_output)
df_sh_state_final = pd.read_hdf(sh_state_final)

# df_output_suews = df_output['SUEWS']
# df_output_suews = df_output['SUEWS']
print(df_sh_output.head())

print(df_sh_output)
# print(pd.DataFrame(df_sh_state_final))
# print(df_sh_output.loc[:, ['QN', 'QS', 'QH', 'QE', 'QF']].describe())
# print(df_sh_output.columns.levels[0])

# list_path_save = sp.save_supy(df_sh_output, df_sh_state_final)

# for file_out in list_path_save:
   # print(file_out.name)

#df_output_suews = df_sh_output.loc[grid, 'SUEWS']
# df_output_suews.to_hdf(
#        suews_output_file,
#        key=f"df_output",
#        complevel=9,
#        complib="blosc:lz4hc",
#    )
