#!/usr/bin/env python3
"""Load a LipidQMap Cardinal HDF5 export and plot an ion image."""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np


def _decode(value) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot an ion image from a LipidQMap Cardinal HDF5 export."
    )
    parser.add_argument("input", type=Path, help="Path to the .h5 file")
    parser.add_argument("mz", type=float, help="Target m/z to plot")
    parser.add_argument(
        "--sample",
        type=int,
        help="1-based index of the sample to display (defaults to the first sample)",
    )
    parser.add_argument(
        "--sample-id",
        type=str,
        help="Sample identifier to display (overrides --sample when provided)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.05,
        help="Allowed absolute m/z difference when matching the feature (default: 0.01)",
    )
    args = parser.parse_args()

    with h5py.File(args.input, "r") as h5:
        mz_values = np.asarray(h5["featureData/mz"][:], dtype=np.float64)
        if mz_values.size == 0:
            raise SystemExit("No features found in featureData/mz.")
        diffs = np.abs(mz_values - args.mz)
        feature_idx = int(diffs.argmin())
        if diffs[feature_idx] > args.tolerance:
            raise SystemExit(
                f"No feature within ±{args.tolerance} m/z of {args.mz:.4f}. "
                f"Closest feature at {mz_values[feature_idx]:.4f} m/z."
            )

        feature_ids = h5["featureData/feature_id"]
        feature_id = _decode(feature_ids[feature_idx])

        intensity_dataset = h5["spectraData/intensity"]
        intensities = np.asarray(intensity_dataset[feature_idx, :], dtype=np.float32)

        samples_group = h5["samples"]
        sample_indices_available = sorted(int(key) for key in samples_group.keys())
        sample_id_map = {
            int(key): _decode(samples_group[key].attrs.get("sample_id", key))
            for key in samples_group.keys()
        }

        target_sample_index: int | None = None
        if args.sample_id:
            for index, sample_id in sample_id_map.items():
                if sample_id == args.sample_id:
                    target_sample_index = index
                    break
            if target_sample_index is None:
                available = ", ".join(sample_id_map.values())
                raise SystemExit(
                    f"Sample id '{args.sample_id}' not found. Available ids: {available}"
                )
        elif args.sample is not None:
            if args.sample not in sample_indices_available:
                available = ", ".join(str(idx) for idx in sample_indices_available)
                raise SystemExit(
                    f"Sample index {args.sample} not found. Available indices: {available}"
                )
            target_sample_index = args.sample
        else:
            target_sample_index = sample_indices_available[0]

        sample_key = str(target_sample_index)
        sample_meta = samples_group[sample_key].attrs
        height = int(sample_meta["height_px"])
        width = int(sample_meta["width_px"])

        pixel_data = h5["pixelData"]
        sample_indices = np.asarray(pixel_data["sample_index"][:], dtype=np.int32)
        mask = sample_indices == target_sample_index
        if not np.any(mask):
            raise SystemExit(f"No pixels recorded for sample index {target_sample_index}.")

        x_coords = np.asarray(pixel_data["x"][:], dtype=np.int32)[mask]
        y_coords = np.asarray(pixel_data["y"][:], dtype=np.int32)[mask]
        sample_intensity = intensities[mask]

        image = np.full((height, width), np.nan, dtype=np.float32)
        x0 = x_coords - 1
        y0 = y_coords - 1
        valid = (x0 >= 0) & (x0 < width) & (y0 >= 0) & (y0 < height)
        image[y0[valid], x0[valid]] = sample_intensity[valid]

    fig, ax = plt.subplots()
    im = ax.imshow(image, origin="upper", cmap="magma")
    sample_label = args.sample_id if args.sample_id else sample_key
    ax.set_title(f"{feature_id} @ {mz_values[feature_idx]:.4f} m/z (sample {sample_label})")
    ax.set_xlabel("x (pixel)")
    ax.set_ylabel("y (pixel)")
    fig.colorbar(im, ax=ax, label="Intensity")
    plt.show()


if __name__ == "__main__":
    main()
