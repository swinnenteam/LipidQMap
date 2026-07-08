import math

import numpy as np
import numpy.typing as npt
from numba import njit

from app.database import LipidDB, LipidSpecies


@njit
def threshold_check(image: npt.NDArray, min_intensity: int, min_pixels: int) -> bool:
    return (image > min_intensity).sum() > min_pixels


def _apply_transparent_mask(
    images: dict[str, npt.NDArray | None],
    mask: npt.NDArray[np.bool_],
) -> dict[str, npt.NDArray | None]:
    masked: dict[str, npt.NDArray | None] = {}
    for key, image in images.items():
        if image is None:
            masked[key] = None
            continue
        result = image.copy()
        if result.shape == mask.shape:
            result[mask] = np.nan
        masked[key] = result
    return masked


def ppm_to_tolerance(ppm: float, mz: float) -> float:
    """Convert ppm mass accuracy to atomic units."""
    return abs(ppm / 1e6 * mz)


def db_isotope_correction(
    database: LipidDB, images: dict[str, npt.NDArray]
) -> dict[str, npt.NDArray]:
    """
    Corrects for isotopic overlap between lipids of the same class but different degrees of saturation.

    This function addresses isobaric interferences where the isotopic peaks of a
    more unsaturated lipid overlap with the monoisotopic peak of a less
    unsaturated lipid within the same class. It accounts for the following cases:

    1.  **M+2 Overlap**: The M+2 isotopologue of a lipid (e.g., from two ¹³C atoms)
        with N double bonds interferes with the monoisotopic peak of a lipid with
        N-1 double bonds (which has two extra hydrogens).
        - Example: The M+2 peak of PC 34:2 contributes to the signal of PC 34:1.

    2.  **M+4 Overlap**: The M+4 isotopologue of a lipid (e.g., from four ¹³C atoms)
        with N double bonds interferes with the monoisotopic peak of a lipid with
        N-2 double bonds (which has four extra hydrogens).
        - Example: The M+4 peak of PC 34:2 contributes to the signal of PC 34:0.

    The function calculates the theoretical isotopic contributions from the more
    unsaturated species and subtracts them from the measured intensity of the
    less unsaturated species.
    """
    # Reuse unchanged arrays and only allocate new arrays for corrected species.
    corrected_images: dict[str, npt.NDArray] = dict(images)
    for s in database.get_species_sorted_for_isotope():
        if s.id_adduct not in images.keys():
            continue
        if s.m2_isotope:
            if s.m2_isotope.id_adduct not in corrected_images:
                continue
            corrected_images[s.id_adduct] = (
                images[s.id_adduct]
                - s.m2_isotope.m2_rel_abundance * corrected_images[s.m2_isotope.id_adduct]
            ).clip(min=0)
            if s.m4_isotope:
                if s.m4_isotope.id_adduct not in corrected_images:
                    continue
                corrected_images[s.id_adduct] = (
                    corrected_images[s.id_adduct]
                    - s.m4_isotope.m4_rel_abundance * corrected_images[s.m4_isotope.id_adduct]
                ).clip(min=0)

    return corrected_images


def na_isotope_correction(
    database: LipidDB,
    images: dict[str, npt.NDArray],
    skipped_classes: set[str] | None = None,
) -> dict[str, npt.NDArray]:
    """
    Isotopic correction for [M+H]+ species with overlap from [M+Na]+ species.
    According to Höring et al. Anal. Chem. 2020, 92, 16, 10966–10970
    https://pubs.acs.org/doi/10.1021/acs.analchem.0c02408
    """
    # Reuse unchanged arrays and only allocate new arrays for corrected species.
    corrected_images: dict[str, npt.NDArray] = dict(images)
    h_na_ratio_ims = dict()

    for h_id, na_id in database.get_hydrogen_sodium_std_pairs():
        if h_id not in images or na_id not in images:
            continue
        ratio_image = np.divide(images[na_id], images[h_id])
        ratio_image[ratio_image == np.inf] = np.nan
        h_na_ratio_ims[h_id] = replace_nan_with_median(ratio_image)

    # correct the [M+H]+
    for s in database.get_species_sorted_for_isotope():
        if "[M+H]+" != s.adduct:
            continue
        if s.id_adduct not in images:
            continue
        if s.na_isotope is not None and s.standard is not None:
            ratio_image = h_na_ratio_ims.get(s.standard.id_adduct)
            overlap_image = corrected_images.get(s.na_isotope.id_adduct)
            if ratio_image is None or overlap_image is None:
                if skipped_classes is not None:
                    skipped_classes.add(s.lipid_class)
                continue
            corrected_images[s.id_adduct] = (
                images[s.id_adduct] - ratio_image * overlap_image
            ).clip(min=0)

    # correct the [M+Na]+
    # e.g. PC 34:1[M+Na]+  = (PC 34:1[M+Na]+) - (PC 36:4[M+H]+)
    for s in database.get_species_sorted_for_isotope():
        if "[M+Na]+" != s.adduct:
            continue
        if s.id_adduct not in images:
            continue
        if s.na_isotope is not None:
            h_species_id_adduct = s.id + " [M+H]+"
            na_species_id_adduct = s.na_isotope.id + " [M+Na]+"
            if (
                h_species_id_adduct not in corrected_images
                or na_species_id_adduct not in corrected_images
            ):
                if skipped_classes is not None:
                    skipped_classes.add(s.lipid_class)
                continue
            corrected_images[na_species_id_adduct] = (
                corrected_images[na_species_id_adduct] - corrected_images[h_species_id_adduct]
            ).clip(min=0)

    return corrected_images


def quantitaton(database: LipidDB, images: dict[str, npt.NDArray]) -> dict[str, npt.NDArray | None]:
    """
    Quantify by dividing the ion images by the ion image of the standard (1 standard per class)
    and multiplying by a user provided factor (standard amount)
    """
    quant_images: dict[str, npt.NDArray | None] = dict()
    for specie in database.get_ids_non_standards():
        if specie.id_adduct not in images:
            quant_images[specie.id_adduct] = None
            continue
        std = specie.standard
        if std is not None and std.id_adduct in images:
            quant_image = np.divide(images[specie.id_adduct], images[std.id_adduct]) * std.amount
            quant_image[quant_image == np.inf] = np.nan
            quant_images[specie.id_adduct] = quant_image
        else:
            quant_images[specie.id_adduct] = None

    return quant_images


def _sum_images_for_neutral(
    database: LipidDB,
    neutral_specie: LipidSpecies,
    images: dict[str, npt.NDArray | None],
) -> npt.NDArray | None:
    """
    Return the summed image for a neutral specie using the provided adduct images.
    """
    adduct_forms = database.get_adduct_species_for_neutral(neutral_specie)
    adduct_images: list[npt.NDArray] = []
    for specie in adduct_forms:
        candidate = images.get(specie.id_adduct)
        if candidate is not None:
            adduct_images.append(candidate)

    if len(adduct_images) == 0:
        image: npt.NDArray | None = None
    elif len(adduct_images) == 1:
        image = adduct_images[0]
    else:
        stacked = np.stack(adduct_images, axis=0)
        if not np.issubdtype(stacked.dtype, np.floating):
            stacked = stacked.astype(np.float32, copy=False)
        all_nan_mask = np.all(np.isnan(stacked), axis=0)
        np.nan_to_num(stacked, copy=False, nan=0.0)
        image = np.sum(stacked, axis=0)
        image[all_nan_mask] = np.nan

    return image


def sum_adducts(
    database: LipidDB,
    images: dict[str, npt.NDArray | None],
    neutral_suffix: str | None = None,
) -> dict[str, npt.NDArray | None]:
    """
    Sum together the different adduct forms of each species.

    Args:
        database: Lipid database providing species relationships.
        images: Mapping from species ID (with adduct) to image data.
        neutral_suffix: Optional suffix used to rename neutral species keys. When
            provided, neutral entries are emitted as ``<id> <neutral_suffix>``.
    """

    result: dict[str, npt.NDArray | None] = {}
    all_species_ids, _ = database.get_all_species(neutral=True)
    neutral_lookup = {specie.id_adduct: specie for specie in database.get_neutral_species()}

    for species_id in all_species_ids:
        specie = database.species[species_id]
        if species_id in neutral_lookup:
            neutral_specie = neutral_lookup[species_id]
            image = _sum_images_for_neutral(
                database=database,
                neutral_specie=neutral_specie,
                images=images,
            )

            key = neutral_specie.id_adduct
            if neutral_suffix is not None:
                key = f"{neutral_specie.id} {neutral_suffix}"
            result[key] = image
        else:
            result[specie.id_adduct] = images.get(specie.id_adduct)

    return result


@njit
def _add_padding(arr, pad_width) -> npt.NDArray:
    """
    Pads the array with NaNs to handle edge cases.
    """
    padded_shape = (arr.shape[0] + 2 * pad_width, arr.shape[1] + 2 * pad_width)
    padded_arr = np.full(padded_shape, np.nan, dtype=arr.dtype)
    padded_arr[pad_width:-pad_width, pad_width:-pad_width] = arr
    return padded_arr


@njit
def replace_nan_with_median(arr: npt.NDArray) -> npt.NDArray:
    """
    Replaces nan values with mean of surrounding window of 3 by 3 pixels, excluding any nan in the window
    """
    # Pad the array with NaNs to handle edge cases
    padded_arr = _add_padding(arr, 1)
    padded_arr = np.where(padded_arr == 0.0, np.nan, padded_arr)  # also replace 0.0 with NaN
    nan_mask = np.isnan(arr) | (arr == 0.0)
    indices = np.argwhere(nan_mask)
    result = np.copy(arr)
    for i, j in indices:
        # Extract surrounding 3x3 window, taking into account offset by 1
        window = padded_arr[i : i + 3, j : j + 3]
        median = np.nanmedian(window)
        if math.isnan(median):  # window contained only NaNs (originally NaN or zero values)
            # Preserve transparency (NaN) for pixels with no data, otherwise keep zeros zero.
            result[i, j] = np.nan if math.isnan(arr[i, j]) else 0.0
        else:
            result[i, j] = median
    return result


@njit
def winsorize_image(image: npt.NDArray | None, upper_percentile: float = 99) -> npt.NDArray | None:
    """
    Set extreme high values to some percentile of the data
    """
    if image is None:
        return None
    upper_bound = np.nanpercentile(image, upper_percentile)
    winsorized_image = np.copy(image)

    # winsorized_image[winsorized_image > upper_bound] = upper_bound
    for i in range(winsorized_image.shape[0]):
        for j in range(winsorized_image.shape[1]):
            if winsorized_image[i, j] > upper_bound:
                winsorized_image[i, j] = upper_bound

    return winsorized_image
