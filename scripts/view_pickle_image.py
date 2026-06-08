#!/usr/bin/env python3
"""Load a LipidQMap Python pickle export and plot an ion image."""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


def _load_images(path: Path) -> dict[str, np.ndarray]:
    import numpy as np

    with path.open("rb") as file:
        data = pickle.load(file)

    if not isinstance(data, dict):
        raise SystemExit(f"Expected a dictionary in {path}, got {type(data).__name__}.")

    images: dict[str, np.ndarray] = {}
    for lipid_id, image in data.items():
        if not isinstance(lipid_id, str):
            raise SystemExit(f"Expected string lipid IDs, got {type(lipid_id).__name__}.")
        array = np.asarray(image)
        if array.ndim != 2:
            raise SystemExit(
                f"Expected a 2-D image for '{lipid_id}', got an array with {array.ndim} dimensions."
            )
        images[lipid_id] = array

    if not images:
        raise SystemExit(f"No ion images found in {path}.")

    return images


def _print_lipids(images: dict[str, np.ndarray]) -> None:
    print("Available lipids:")
    for index, (lipid_id, image) in enumerate(images.items(), start=1):
        print(f"{index:4d}. {lipid_id}  shape={image.shape}  dtype={image.dtype}")


def _select_lipid(images: dict[str, np.ndarray], requested_lipid: str | None) -> str:
    if requested_lipid:
        if requested_lipid in images:
            return requested_lipid
        raise SystemExit(f"Lipid '{requested_lipid}' not found in this pickle file.")

    choice = input("\nEnter lipid ID or list number to plot: ").strip()
    if choice in images:
        return choice

    try:
        index = int(choice)
    except ValueError:
        raise SystemExit(f"Lipid '{choice}' not found in this pickle file.") from None

    lipid_ids = list(images)
    if 1 <= index <= len(lipid_ids):
        return lipid_ids[index - 1]

    raise SystemExit(f"List number {index} is outside the available range 1-{len(lipid_ids)}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "List lipids in a LipidQMap .pkl export and plot one 2-D quantitative ion image. "
            "Only open pickle files from trusted sources."
        )
    )
    parser.add_argument("input", type=Path, help="Path to a LipidQMap .pkl export")
    parser.add_argument(
        "lipid",
        nargs="?",
        help="Lipid/species ID to plot. If omitted, the script prompts after listing lipids.",
    )
    parser.add_argument(
        "--cmap",
        default="magma",
        help="Matplotlib colormap to use for the image (default: magma)",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list available lipids; do not prompt or show a plot",
    )
    args = parser.parse_args()

    images = _load_images(args.input)
    _print_lipids(images)

    if args.list_only:
        return

    lipid_id = _select_lipid(images, args.lipid)
    image = images[lipid_id]

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    im = ax.imshow(image, origin="upper", cmap=args.cmap)
    ax.set_title(lipid_id)
    ax.set_xlabel("x (pixel)")
    ax.set_ylabel("y (pixel)")
    fig.colorbar(im, ax=ax, label="Intensity")
    plt.show()


if __name__ == "__main__":
    main()
