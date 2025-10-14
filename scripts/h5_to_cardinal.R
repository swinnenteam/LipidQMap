#!/usr/bin/env Rscript
# Minimal script to load a LipidQMap Cardinal HDF5 export into Cardinal.

library(rhdf5)
library(Cardinal)

h5_path <- file.choose(new = FALSE)

feature_df <- h5read(h5_path, "featureData")
position_df <- PositionDataFrame(
  run = h5read(h5_path, "pixelData/run"),
  coord = data.frame(
    x = h5read(h5_path, "pixelData/x"),
    y = h5read(h5_path, "pixelData/y")
  )
)

msi <- MSImagingExperiment(
  spectraData = h5read(h5_path, "spectraData/intensity", native = TRUE),
  featureData = MassDataFrame(mz = feature_df$mz, featureData = feature_df),
  pixelData = position_df,
  centroided = TRUE
)

print(msi)
image(msi, mz=798.54096)
