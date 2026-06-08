# LipidQMap Export Formats

This document describes the file structures written by LipidQMap export actions.

## Python Pickle Export

The Python pickle export is available from **File > Export Python pickle...**. It writes one `.pkl` file per loaded sample into the selected output folder.

```text
<selected-folder>/
|-- <sample_1>.pkl
|-- <sample_2>.pkl
`-- ...
```

Each `.pkl` file contains one Python dictionary written with `pickle.dump(...)`.

```python
dict[str, numpy.ndarray]
```

The dictionary structure is:

| Key | Value |
| --- | --- |
| LipidQMap species ID, matching the species table display ID | 2-D quantitative ion image as a `numpy.ndarray` |

Important details:

- Only the quantitative image collection is exported.
- Species with no quantitative image for a sample are omitted from that sample's dictionary.
- Raw images, isotope-corrected images, spectra, coordinates, and metadata are not included.
- Summed adduct images are included as separate dictionary entries when present in LipidQMap.
- The export is sample-local: each `.pkl` file contains images for one sample only.

Example reader:

```python
import pickle

with open("sample_1.pkl", "rb") as fh:
    images = pickle.load(fh)

for species_id, image in images.items():
    print(species_id, image.shape, image.dtype)
```

## Cardinal HDF5 Export

The Cardinal HDF5 export is available from **File > Export Cardinal h5...**. It writes a single `.h5` or `.hdf5` file containing all selected samples and features in a Cardinal-compatible HDF5 layout.

```text
<selected-file>.h5
```

The exported file is a standard HDF5 container with these top-level objects:

```text
/
|-- attrs: format, creator, creator_version, image_type
|-- spectraData/
|   `-- intensity
|-- pixelData/
|   |-- pixel_index
|   |-- x
|   |-- y
|   |-- sample_index
|   |-- run
|   |-- sample_id
|   `-- coord
|-- featureData/
|   |-- feature_index
|   |-- feature_id
|   |-- mz
|   |-- lipid_class
|   |-- adduct
|   |-- neutral_id
|   `-- is_standard
`-- samples/
    |-- 1/
    |-- 2/
    `-- ...
```

Root attributes:

| Attribute | Meaning |
| --- | --- |
| `format` | Always `Cardinal::HDF5` |
| `creator` | Always `LipidQMap` |
| `creator_version` | LipidQMap version that wrote the file |
| `image_type` | One of `quant`, `isotope`, or `raw` |

The core intensity matrix is stored at `spectraData/intensity` as a 2-D `float32` array:

```text
(n_features, n_pixels)
```

Rows align with `featureData`; columns align with `pixelData`. The dataset uses gzip compression level 4 with the shuffle filter, and includes HDF5 dimension scales linking:

- axis 0 to `featureData/feature_id`
- axis 1 to `pixelData/pixel_index`

Pixel coordinates are 1-based, matching Cardinal conventions. Dense images are flattened in row-major order. Sparse coordinate exports use the original pixel coordinate table.

Sample metadata is stored as attributes on `samples/<index>` groups. Each sample group includes:

| Attribute | Meaning |
| --- | --- |
| `sample_id` | Original sample name |
| `height_px` | Image height in pixels |
| `width_px` | Image width in pixels |
| `n_pixels` | Number of exported pixels for that sample |
| `min_x`, `max_x`, `min_y`, `max_y` | Sparse coordinate bounds, present only when sparse coordinates are exported |
| `pixel_size_um_x`, `pixel_size_um_y` | Optional physical pixel size metadata |

For the full HDF5 schema, including dataset types and compatibility notes, see [cardinal_hdf5_format.md](cardinal_hdf5_format.md).

## R Cardinal Import

LipidQMap includes a minimal R reader at `scripts/h5_to_cardinal.R`. It reads the HDF5 export with `rhdf5` and constructs a Cardinal `MSImagingExperiment`.

The reader uses:

- `featureData` for m/z and feature metadata
- `pixelData/run`, `pixelData/x`, and `pixelData/y` for pixel metadata
- `spectraData/intensity` for the feature-by-pixel intensity matrix

Minimal structure:

```r
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
```

## SCiLS Export

The SCiLS export writes processed ion images directly into an existing `.slx` SCiLS Lab dataset through the SCiLS Lab Python API. It does not create a standalone file structure in the selected folder.

The export creates external feature lists in the selected SCiLS dataset. Feature values are matched to SCiLS spot IDs using the loaded sample's coordinates or spot identifiers.

Important details:

- SCiLS export is only available on Windows with the SCiLS Lab API installed.
- The selected `.slx` dataset must already exist.
- Exported feature lists are labeled with the LipidQMap sample/image type.
- Species without the requested processed image are skipped.
