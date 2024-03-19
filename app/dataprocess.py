import numpy as np
from pyimzml.ImzMLParser import ImzMLParser, getionimage

from app.database import LipidDB


def load_ion_images(
    database: LipidDB, imzml: ImzMLParser, classes: list[str], tolerance=0.005
) -> dict[str, np.array]:
    images: dict[str, np.array] = dict()
    for id, mz in database.get_all_species(classes):
        images[id] = getionimage(imzml, mz_value=mz, tol=tolerance)
    return images


def isotope_correction(
    database: LipidDB, images: dict[str, np.array], classes: list[str]
) -> dict[str, np.array]:
    corrected_images: dict[str, np.array] = dict()
    for species_id in database.get_ids_sorted_for_isotope(classes=classes):
        m2_isotope = database.get_M2_isotope_ID(id=species_id)
        if m2_isotope:
            corrected_images[species_id] = (
                images[species_id]
                - database.get_M2_isotope_percent(id=m2_isotope) * images[m2_isotope]
            )
        else:
            corrected_images[species_id] = np.copy(images[species_id])

    return corrected_images


def quantitaton(
    database: LipidDB, images: dict[str, np.array], classes: list[str]
) -> dict[str, np.array]:
    quant_images: dict[str, np.array] = dict()
    for species_id in database.get_ids_non_standards(classes=classes):
        standard_id, standard_amount = database.get_standard(id=species_id)
        quant_images[species_id] = (
            np.divide(images[species_id], images[standard_id]) * standard_amount
        )

    return quant_images
