pkgs = c("tidyverse", "ggprism", "extrafont", "remotes", "corrplot", "descr", "car", 
         "stargazer", "coefplot", "sf", "tmap", "rgdal", "rgeos", "spdep")
install.packages(pkgs)

if (!require("BiocManager", quietly = TRUE))
  install.packages("BiocManager")

BiocManager::install("rhdf5")
library(rhdf5)

inst = lapply(pkgs, library, character.only = TRUE)
inst

h5_file <- "C:/Users/Danish/OneDrive - University College London/dissertation_data/lcz-supy-global-data/consolidated_outputs/GreaterKL-2017_Y1_M2sp_3sf_R1_consolidated.h5"

df = H5Fopen(h5_file)

df$df
