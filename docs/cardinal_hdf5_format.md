LipidQMap writes MSI exports as HDF5 containers that follow the [`Cardinal::HDF5`](https://cardinalmsi.org) conventions. This document explains the layout from a consumer’s point of view so external tools can read the data without needing to reference LipidQMap internals.

## Overview

- File extension: `.h5` or `.hdf5` (standard HDF5)
- Compression: `spectraData/intensity` uses GZIP level 4 with the shuffle filter
- Coordinate system: 1-based pixel and coordinate indices (matches Cardinal)
- Feature order: ascending by `mz`

Top-level objects:

- Attributes describing the file
- Group `spectraData`
- Group `pixelData`
- Group `featureData`
- Group `samples`

## Root-level attributes

| Attribute          | Type     | Meaning                                                |
|--------------------|----------|--------------------------------------------------------|
| `format`           | string   | Always `Cardinal::HDF5`                                |
| `creator`          | string   | `LipidQMap`                                            |
| `creator_version`  | string   | LipidQMap semantic version used to generate the file   |
| `image_type`       | string   | One of `quant`, `isotope`, or `raw`; indicates which image stack was exported |

## `spectraData`

Holds the feature-by-pixel intensity matrix.

- `intensity` *(dataset)*: 2-D `float32` array shaped `(n_features, n_pixels)`
  - Attributes:
    - `layout`: string `feature_by_pixel`
  - Dimension scales:
    - Axis 0 is labeled `feature_id` and linked to `featureData/feature_id`
    - Axis 1 is labeled `pixel_index` and linked to `pixelData/pixel_index`
- Group attributes:
  - `n_features`: integer count of exported features
  - `n_spectra`: integer count of exported pixels

## `pixelData`

Metadata for every exported pixel, stored column-wise. All columns share the same row order and align with the second dimension of `spectraData/intensity`.

| Dataset        | Type        | Description                                                                    |
|----------------|-------------|--------------------------------------------------------------------------------|
| `pixel_index`  | int64       | 1-based identifier for each pixel (dimension scale for intensity axis 1)      |
| `x`            | int64       | 1-based X coordinate (columns)                                                 |
| `y`            | int64       | 1-based Y coordinate (rows)                                                    |
| `sample_index` | int64       | 1-based index referencing `samples/<index>`                                   |
| `run`          | UTF-8 str   | Human-readable sample/run label                                                |
| `sample_id`    | UTF-8 str   | Same as `run`; provided for compatibility with Cardinal naming conventions    |

Additional datasets and attributes:

- Group attribute `columns`: ordered list of column names above.
- `coord` *(dataset)*: 2-D `int32` array with shape `(n_pixels, 2)` containing `[x, y]` pairs. Its first dimension attaches to the `pixel_index` scale and has attribute `columns = ["x", "y"]`. This offers a compact coordinate table for consumers that support matrix reads.

## `featureData`

Per-feature metadata aligned with the first dimension of `spectraData/intensity`.

| Dataset        | Type        | Description                                                                |
|----------------|-------------|----------------------------------------------------------------------------|
| `feature_index`| int64       | 1-based ordinal position (matches Cardinal)                                |
| `feature_id`   | UTF-8 str   | Display identifier used throughout LipidQMap (e.g., `PC 34:1 [M+H]+`)      |
| `mz`           | float32     | Monoisotopic m/z used for sorting                                          |
| `lipid_class`  | UTF-8 str   | Lipid class pulled from the reference database                             |
| `adduct`       | UTF-8 str   | Ion adduct                                                                 |
| `neutral_id`   | UTF-8 str   | Identifier of the neutral lipid species in the database                    |
| `is_standard`  | bool        | `True` when the species is marked as an internal standard                  |

The group attribute `columns` lists the dataset names in order.

## `samples`

Contains one subgroup per exported sample, keyed by 1-based index (`"1"`, `"2"`, …). Each subgroup is attribute-only; there are no nested datasets.

| Attribute           | Type    | Description                                                               |
|---------------------|---------|---------------------------------------------------------------------------|
| `sample_id`         | string  | Original sample name (matches `pixelData.sample_id`)                      |
| `height_px`         | integer | Image height in pixels (raw section grid)                                 |
| `width_px`          | integer | Image width in pixels                                                     |
| `n_pixels`          | integer | Number of pixels written for the sample                                   |
| `min_x`, `max_x`    | integer | Bounding box of provided coordinates (only present for sparse exports)    |
| `min_y`, `max_y`    | integer | Bounding box of provided coordinates (only present for sparse exports)    |
| `pixel_size_um_x`   | float   | Optional physical pixel size along X (micrometres), when known            |
| `pixel_size_um_y`   | float   | Optional physical pixel size along Y (micrometres), when known            |

When LipidQMap exports a dense rectangular image (no sparse coordinates), `min_*`/`max_*` attributes are omitted and `n_pixels` equals `height_px × width_px`.

## Tips

- Treat `pixel_index` and `feature_index` as the authoritative join keys between groups.
- Check the root `image_type` attribute to understand whether intensities are quantitative, isotope-corrected, or raw.
- Use the HDF5 dimension scales to align spectra and metadata without assuming dataset order.
