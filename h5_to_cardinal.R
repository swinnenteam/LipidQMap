#!/usr/bin/env Rscript
# Minimal script to load a LipidQMap Cardinal HDF5 export into Cardinal.

library(rhdf5)
library(Cardinal)

h5_path <- file.choose(new = FALSE)

feature_df <- as.data.frame(lapply(h5read(h5_path, "featureData"), as.vector), stringsAsFactors = FALSE)
pixel_df <- as.data.frame(lapply(h5read(h5_path, "pixelData"), as.vector), stringsAsFactors = FALSE)

intensity <- h5read(h5_path, "spectraData/intensity", native = TRUE)
dimnames(intensity) <- list(feature_df$feature_id, as.character(pixel_df$pixel_index))

mass_df <- MassDataFrame(mz = feature_df$mz, featureData = feature_df)
coord_df <- data.frame(x = as.numeric(pixel_df$x), y = as.numeric(pixel_df$y))
position_df <- PositionDataFrame(run = factor(pixel_df$run), coord = coord_df)

msi <- MSImagingExperiment(
  spectraData = intensity,
  featureData = mass_df,
  pixelData = position_df,
  centroided = TRUE
)

print(msi)
