# Changelog

All notable changes to LipidQMap are documented here. The project follows
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-08-26


### Added

- Import MSI data from AnnData (`.h5ad`) and MuData (`.h5mu`) files, including
  multi-sample data, spatial coordinates, foreground masks, pixel-size metadata,
  and a choice between raw and batch-corrected matrices when available.
- Export raw, isotope-corrected, or quantitative data to a Python pickle file,
  with options to limit the export to selected features and include summed-adduct
  images.
- Export processed images directly to an existing SCiLS Lab dataset on Windows.
  Raw, isotope-corrected, and quantitative feature lists can be exported for one
  or more samples, with control over selected features and adduct types.
- Choose whether Cardinal HDF5 exports contain selected features only and whether
  they include summed-adduct images.
- Copy the species export-selection table to the clipboard and paste an edited,
  Excel-compatible selection back into LipidQMap.
- Select ion images automatically using connected, feature-like regions above a
  robust background-noise estimate. The original intensity-and-pixel-count method
  remains available in Settings.

### Changed

- Detect the polarity of imzML files automatically. Files without polarity
  metadata prompt for a manual choice instead.
- Pair matching positive- and negative-mode imzML files into one logical sample,
  with separate online-calibration reference masses for each polarity.
- Recalculate neutral summed-adduct images from the adducts currently selected in
  the species table and update affected plots immediately when the selection
  changes.
- Preserve physical pixel dimensions throughout import, display, transformation,
  and export. Non-square pixels now render with the correct aspect ratio, and 1:1
  TIFF exports include pixel-size metadata when available.
- Improve the sizing and whitespace of individual and panel image exports.
- Improve database validation and error messages for missing standard amounts,
  invalid species references, and incomplete adduct definitions. H/Na overlap
  correction now skips unsupported lipid classes while continuing to process the
  remaining data.
- Document the Cardinal HDF5, Python pickle, and SCiLS export formats.

### Fixed

- Cardinal HDF5 exports no longer substitute isotope-corrected or raw data when a
  requested quantitative image is unavailable.
- Summed-adduct images now ignore `NaN` values, use only selected adducts, and are
  refreshed correctly after selection changes.
- Average spectra switch to the correct polarity when viewing combined
  positive/negative samples.
- Image rotation, Gaussian filtering, padding, color scaling, and panel layout no
  longer produce incorrect orientations, dimensions, or empty space in affected
  cases.
- SCiLS exports handle multiple samples more reliably, report connection and
  license errors clearly, and leave the application usable after a failed export.
- Numeric fields in the standard calculator handle decimal separators correctly
  across system locales.
- Packaged applications include the modules required by the new import and export
  workflows.

### Performance

- Store processed images as 32-bit floating-point arrays and avoid unnecessary
  deep copies, reducing memory use when working with large datasets.

## [0.1.0] - 2025-10-13

- Initial public release.
