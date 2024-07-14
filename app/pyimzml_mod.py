import re
import sys
from pathlib import Path
from random import sample
from typing import Any, BinaryIO, Callable, Iterator
from warnings import warn

import numpy as np
import numpy.typing as npt
from lxml.etree import _Element, iterparse
from numba import njit, prange
from pyimzml.ImzMLParser import PRECISION_DICT, SIZE_DICT, _bisect_spectrum, _get_cv_param
from pyimzml.metadata import Metadata, SpectrumData


class ImzMLParser:
    """
    Parser for imzML 1.1.0 files (see specification here:
    https://ms-imaging.org/wp-content/uploads/2009/08/specifications_imzML1.1.0_RC1.pdf ).

    In the original PyimzML ImzMLParser, the binary file is read in every call to getspectrum(i).
    In this modified parser, the spectra are read into memory upon initialisation, after which the
    connection to the file is closed. This greatly speeds up the program when many calls to
    getspectrum(i) are necaissary.
    Use enumerate(parser.coordinates) to get all coordinates with their
    respective index. Coordinates are always 3-dimensional. If the third spatial dimension is not present in
    the data, it will be set to zero.

    The global metadata fields in the imzML file are stored in parser.metadata.
    Spectrum-specific metadata fields are not stored by default due to avoid memory issues,
    use the `include_spectra_metadata` parameter if spectrum-specific metadata is needed.
    """

    def __init__(
        self,
        filename: str,
        ibd_file: str | None = "auto",
        include_spectra_metadata: str | list[str] | None = None,
    ):
        """
        Opens the two files corresponding to the file name, reads the entire .imzML
        file and extracts required attributes. Does not read any binary data, yet.

        :param filename:
            name of the XML file. Must end with .imzML. Binary data file must be named equally but ending with .ibd
            Alternatively an open file or Buffer Protocol object can be supplied, if ibd_file is also supplied
        :param ibd_file:
            Set to "auto" to infer it from the imzml filename.
            Set to None if no data from the .ibd file is needed (getspectrum calls will not work)
        :param include_spectra_metadata:
            None, 'full', or a list/set of accession IDs.
            If 'full' is given, parser.spectrum_full_metadata will be populated with a list of
                complex objects containing the full metadata for each spectrum.
            If a list or set is given, parser.spectrum_metadata_fields will be populated with a dict mapping
                accession IDs to lists. Each list will contain the values for that accession ID for
                each spectrum. Note that for performance reasons, this mode only searches the
                spectrum itself for the value. It won't check any referenced referenceable param
                groups if the accession ID isn't present in the spectrum metadata.
        """
        # ElementTree requires the schema location for finding tags (why?) but
        # fails to read it from the root element. As this should be identical
        # for all imzML files, it is hard-coded here and prepended before every tag
        self.sl: str = "{http://psi.hupo.org/ms/mzml}"
        # maps each imzML number format to its struct equivalent
        self.precisionDict: dict[str, str] = dict(PRECISION_DICT)
        # maps each number format character to its amount of bytes used
        self.sizeDict: dict[str, int] = dict(SIZE_DICT)
        self.filename: str = filename
        self.mzOffsets: list[int] = []
        self.intensityOffsets: list[int] = []
        self.mzLengths: list[int] = []
        self.intensityLengths: list[int] = []
        # list of all (x,y,z) coordinates as tuples.
        self.coordinates: list[tuple[int, int, int]] = []
        self.root: _Element
        self.metadata: Metadata | None = None
        self.polarity: str
        self.spectrum_mode: str
        if include_spectra_metadata == "full":
            self.spectrum_full_metadata: list[Any] = []
        elif include_spectra_metadata is not None:
            self.spectrum_metadata_fields: dict[str, list[Any]] = {
                k: [] for k in set(include_spectra_metadata)
            }

        self.mzGroupId: str | None = None
        self.intGroupId: str | None = None
        self.mzPrecision: str
        self.intensityPrecision: str
        self.iterparse: Callable = iterparse
        self.__iter_read_spectrum_meta(include_spectra_metadata)
        if ibd_file == "auto":
            # name of the binary file
            ibd_filename = self._infer_bin_filename(self.filename)
            self.m: BinaryIO = open(ibd_filename, "rb")

        # Dict for basic imzML metadata other than those required for reading
        # spectra. See method __readimzmlmeta()
        self.imzmldict: dict[str, str | int | float] = self.__readimzmlmeta()
        self.imzmldict["max count of pixels z"] = np.asarray(self.coordinates)[:, 2].max()
        # load the spectra and close the .ibd file
        self.spectra: list[npt.NDArray] = self._loadspectra()
        self.m.close()
        self.root = None

    @staticmethod
    def _infer_bin_filename(imzml_dir: str) -> str:
        imzml_path = Path(imzml_dir)
        ibd_path = [
            f
            for f in imzml_path.parent.glob("*")
            if re.match(r".+\.ibd", str(f), re.IGNORECASE) and f.stem == imzml_path.stem
        ][0]
        return str(ibd_path)

    def __iter_read_spectrum_meta(self, include_spectra_metadata: str | list[str] | None) -> None:
        """
        This method should only be called by __init__. Reads the data formats, coordinates and offsets from
        the .imzML file and initializes the respective attributes. While traversing the XML tree, the per-spectrum
        metadata is pruned, i.e. the <spectrumList> element(s) are left behind empty.

        Supported accession values for the number formats: "MS:1000521", "MS:1000523", "IMS:1000141" or
        "IMS:1000142". The string values are "32-bit float", "64-bit float", "32-bit integer", "64-bit integer".
        """
        mz_group = int_group = None
        slist = None
        elem_iterator: Iterator = self.iterparse(self.filename, events=("start", "end"))

        if sys.version_info > (3,):
            _, self.root = next(elem_iterator)
        else:
            _, self.root = elem_iterator.next()

        is_first_spectrum = True

        for event, elem in elem_iterator:
            if elem.tag == self.sl + "spectrumList" and event == "start":
                self.__process_metadata()
                slist = elem
            elif elem.tag == self.sl + "spectrum" and event == "end":
                self.__process_spectrum(elem, include_spectra_metadata)
                if is_first_spectrum:
                    self.__read_polarity(elem)
                    self.__read_spectrum_mode(elem)
                    is_first_spectrum = False
                slist.remove(elem)
        self.__fix_offsets()

    def __fix_offsets(self) -> None:
        # clean up the mess after morons who use signed 32-bit where unsigned 64-bit is appropriate
        def fix(array):
            fixed = []
            delta = 0
            prev_value = float("nan")
            for value in array:
                if value < 0 and prev_value >= 0:
                    delta += 2**32
                fixed.append(value + delta)
                prev_value = value
            return fixed

        self.mzOffsets = fix(self.mzOffsets)
        self.intensityOffsets = fix(self.intensityOffsets)

    def __process_metadata(self) -> None:
        if self.metadata is None:
            self.metadata = Metadata(self.root)
            for param_id, param_group in self.metadata.referenceable_param_groups.items():
                if "m/z array" in param_group.param_by_name:
                    self.mzGroupId = param_id
                    for name, dtype in self.precisionDict.items():
                        if name in param_group.param_by_name:
                            self.mzPrecision = dtype
                if "intensity array" in param_group.param_by_name:
                    self.intGroupId = param_id
                    for name, dtype in self.precisionDict.items():
                        if name in param_group.param_by_name:
                            self.intensityPrecision = dtype
            if not hasattr(self, "mzPrecision"):
                raise RuntimeError("Could not determine m/z precision")
            if not hasattr(self, "intensityPrecision"):
                raise RuntimeError("Could not determine intensity precision")

    def __process_spectrum(self, elem, include_spectra_metadata):
        arrlistelem = elem.find("%sbinaryDataArrayList" % self.sl)
        mz_group = None
        int_group = None
        for e in arrlistelem:
            ref = e.find("%sreferenceableParamGroupRef" % self.sl).attrib["ref"]
            if ref == self.mzGroupId:
                mz_group = e
            elif ref == self.intGroupId:
                int_group = e
        self.mzOffsets.append(int(_get_cv_param(mz_group, "IMS:1000102")))
        self.mzLengths.append(int(_get_cv_param(mz_group, "IMS:1000103")))
        self.intensityOffsets.append(int(_get_cv_param(int_group, "IMS:1000102")))
        self.intensityLengths.append(int(_get_cv_param(int_group, "IMS:1000103")))
        scan_elem = elem.find("%sscanList/%sscan" % (self.sl, self.sl))
        x = _get_cv_param(scan_elem, "IMS:1000050")
        y = _get_cv_param(scan_elem, "IMS:1000051")
        z = _get_cv_param(scan_elem, "IMS:1000052")
        if z is not None:
            self.coordinates.append((int(x), int(y), int(z)))
        else:
            self.coordinates.append((int(x), int(y), 1))

        if include_spectra_metadata == "full":
            self.spectrum_full_metadata.append(
                SpectrumData(elem, self.metadata.referenceable_param_groups)
            )
        elif include_spectra_metadata:
            for param in include_spectra_metadata:
                value = _get_cv_param(elem, param, deep=True, convert=True)
                self.spectrum_metadata_fields[param].append(value)

    def __read_polarity(self, elem):
        # It's too slow to always check all spectra, so first check the referenceable_param_groups
        # in the header to see if they indicate the polarity. If not, try to detect it from
        # the first spectrum's full metadata.
        # LIMITATION: This won't detect "mixed" polarity if polarity is only specified outside the
        # referenceable_param_groups.
        param_groups = self.metadata.referenceable_param_groups.values()
        spectrum_metadata = SpectrumData(elem, self.metadata.referenceable_param_groups)
        has_positive = (
            any("positive scan" in group for group in param_groups)
            or "positive scan" in spectrum_metadata
        )
        has_negative = (
            any("negative scan" in group for group in param_groups)
            or "negative scan" in spectrum_metadata
        )
        if has_positive and has_negative:
            self.polarity = "mixed"
        elif has_positive:
            self.polarity = "positive"
        elif has_negative:
            self.polarity = "negative"

    def __read_spectrum_mode(self, elem):
        """
        This method checks for centroid (MS:1000127) / profile (MS:1000128) mode information.

        It's too slow to always check all spectra, so first check the referenceable_param_groups
        in the header to see if they indicate the spectrum mode.
        If not, try to detect it from the first spectrum's full metadata.
        """
        param_groups = self.metadata.referenceable_param_groups.values()
        spectrum_metadata = SpectrumData(elem, self.metadata.referenceable_param_groups)

        profile_mode = (
            any("profile spectrum" in group for group in param_groups)
            or "profile spectrum" in spectrum_metadata
        )
        centroid_mode = (
            any("centroid spectrum" in group for group in param_groups)
            or "centroid spectrum" in spectrum_metadata
        )

        if profile_mode:
            self.spectrum_mode = "profile"
        elif centroid_mode:
            self.spectrum_mode = "centroid"

    def __readimzmlmeta(self) -> dict[str, str | int | float]:
        """
        DEPRECATED - use self.metadata instead, as it has much greater detail and allows for
        multiple scan settings / instruments.

        This method should only be called by __init__. Initializes the imzmldict with frequently used metadata from
        the .imzML file.

        :return d:
            dict containing above mentioned meta data
        :rtype:
            dict
        :raises Warning:
            if an xml attribute has a number format different from the imzML specification
        """
        d = {}
        scan_settings_list_elem = self.root.find("%sscanSettingsList" % self.sl)
        instrument_config_list_elem = self.root.find("%sinstrumentConfigurationList" % self.sl)
        scan_settings_params = [
            ("max count of pixels x", "IMS:1000042"),
            ("max count of pixels y", "IMS:1000043"),
            ("max dimension x", "IMS:1000044"),
            ("max dimension y", "IMS:1000045"),
            ("pixel size x", "IMS:1000046"),
            ("pixel size y", "IMS:1000047"),
            ("matrix solution concentration", "MS:1000835"),
        ]
        instrument_config_params = [
            ("wavelength", "MS:1000843"),
            ("focus diameter x", "MS:1000844"),
            ("focus diameter y", "MS:1000845"),
            ("pulse energy", "MS:1000846"),
            ("pulse duration", "MS:1000847"),
            ("attenuation", "MS:1000848"),
        ]

        for name, accession in scan_settings_params:
            try:
                val = _get_cv_param(scan_settings_list_elem, accession, deep=True, convert=True)
                if val is not None:
                    d[name] = val
            except ValueError:
                warn(Warning('Wrong data type in XML file. Skipped attribute "%s"' % name))

        for name, accession in instrument_config_params:
            try:
                val = _get_cv_param(instrument_config_list_elem, accession, deep=True, convert=True)
                if val is not None:
                    d[name] = val
            except ValueError:
                warn(Warning('Wrong data type in XML file. Skipped attribute "%s"' % name))
        return d

    def get_physical_coordinates(self, i: int) -> tuple[float, float]:
        """
        For a pixel index i, return the real-world coordinates in nanometers.

        This is equivalent to multiplying the image coordinates of the given pixel with the pixel size.

        :param i: the pixel index
        :return: a tuple of x and y coordinates.
        :rtype: Tuple[float]
        :raises KeyError: if the .imzML file does not specify the attributes "pixel size x" and "pixel size y"
        """
        try:
            pixel_size_x = float(self.imzmldict["pixel size x"])
            pixel_size_y = float(self.imzmldict["pixel size y"])
        except KeyError:
            raise KeyError("Could not find all pixel size attributes in imzML file")
        image_x, image_y = self.coordinates[i][:2]
        return image_x * pixel_size_x, image_y * pixel_size_y

    def _loadspectra(self) -> list[npt.NDArray]:
        """
        Reads all the spectra from the .ibd file into memory.

        Output:
        list[numpy.ndarray[x,y,z]]
        x: spectrum index
        y: mz_array: numpy.ndarray
            Sequence of m/z values representing the horizontal axis of the desired mass
            spectrum
        z: intensity_array: numpy.ndarray
            Sequence of intensity values corresponding to mz_array
        """
        spectra = []
        for index, _ in enumerate(self.coordinates):
            mz_bytes, intensity_bytes = self.get_spectrum_as_string(index)
            mz_array = np.frombuffer(mz_bytes, dtype=self.mzPrecision)
            intensity_array = np.frombuffer(intensity_bytes, dtype=self.intensityPrecision)
            spectra.append(np.vstack((mz_array, intensity_array)))
        return spectra

    def getspectrum(self, index: int) -> npt.NDArray:
        """get spectrum at index"""
        return self.spectra[index]

    def get_spectrum_as_string(self, index: int) -> tuple[bytes, bytes]:
        """
        Reads m/z array and intensity array of the spectrum at specified location
        from the binary file as a byte string. The string can be unpacked by the struct
        module. To get the arrays as numbers, use getspectrum

        :param index:
            Index of the desired spectrum in the .imzML file
        :rtype: Tuple[bytes, bytes]

        Output:

        mz_string:
            string where each character represents a byte of the mz array of the
            spectrum
        intensity_string:
            string where each character represents a byte of the intensity array of
            the spectrum
        """
        offsets = [self.mzOffsets[index], self.intensityOffsets[index]]
        lengths = [self.mzLengths[index], self.intensityLengths[index]]
        lengths[0] *= self.sizeDict[self.mzPrecision]
        lengths[1] *= self.sizeDict[self.intensityPrecision]
        self.m.seek(offsets[0])
        mz_string = self.m.read(lengths[0])
        self.m.seek(offsets[1])
        intensity_string = self.m.read(lengths[1])
        return mz_string, intensity_string

    def recallibrate(
        self,
        mz: float,
        tol: float = 0.1,
        min_intensity: int = 10000,
    ) -> None:
        """
        Recallibrates the spectra. This is done by offsetting per image row the average difference
        between the given mz: float and the closest matching measured mz.
        """
        tol = abs(tol)
        im = np.full(
            [
                int(self.imzmldict["max count of pixels y"]),
                int(self.imzmldict["max count of pixels x"]),
            ],
            np.nan,
        )
        for i, (x, y, z_) in enumerate(self.coordinates):
            mzs, ints = map(lambda x: np.asarray(x), self.getspectrum(i))
            min_i, max_i = _bisect_spectrum(mzs, mz, tol)
            intensity_values = ints[min_i : max_i + 1]
            mz_values = mzs[min_i : max_i + 1]
            threshold = intensity_values > min_intensity
            intensity_values = intensity_values[threshold]
            mz_values = mz_values[threshold]
            im[y - 1, x - 1] = (
                mz_values[np.argmax(intensity_values)] if mz_values.size != 0 else np.nan
            )
        offsets = mz - np.nanmean(im, axis=1)
        offsets[np.isnan(offsets)] = 0
        for i, (x, y, z_) in enumerate(self.coordinates):
            self.spectra[i][0] = self.spectra[i][0] + offsets[y - 1]
        return None


def get_ion_images(
    p: ImzMLParser,
    mzs: list[float],
    tolerances: list[float],
) -> npt.NDArray:
    """
    Helper function for get_ion_images_numba, which uses the Numba library which isn't compatible
    with complex objects such as ImzMLParser.

    :param p:
        the ImzMLParser (or anything else with similar attributes) for the desired dataset
    :param mzs:
        list of m/z values for which the ion images shall be returned
    :param tolerances:
        Absolute tolerance for the m/z value, such that all ions with values
        mz-|tol| <= x <= mz+|tol| are included.

    :return:
        numpy matrix with each element representing the ion intensity in this
        pixel.
    """
    img_shape = (
        int(p.imzmldict["max count of pixels x"]),
        int(p.imzmldict["max count of pixels y"]),
    )
    return get_ion_images_numba(
        coordinates=p.coordinates,
        spectra=p.spectra,
        img_shape=img_shape,
        mzs=mzs,
        tolerances=tolerances,
    )


@njit(parallel=True)
def get_ion_images_numba(
    coordinates: list[tuple[int, int, int]],
    spectra: list[npt.NDArray],
    img_shape: tuple[int, int],
    mzs: list[float],
    tolerances: list[float],
) -> npt.NDArray:
    """
    Get an image representation of the intensity distribution
    of the ion with specified m/z value. Images are assumed 2D


    By default, the intensity values within the tolerance region are summed.

    :param coordinates:
        list of (x,y,z) pixel coordinates for each spectrum
    :param spectra:
        list of NDarrays each containing the mz array and intensity array of a spectrum
    :param img_shape:
        tuple of number of pixels in the x and y dimension of the image
    :param mzs:
        list of m/z values for which the ion images shall be returned
    :param tolerances:
        Absolute tolerance for the m/z value, such that all ions with values
        mz-|tol| <= x <= mz+|tol| are included.

    :return:
        numpy matrix with each element representing the ion intensity in this
        pixel.
    """
    mzs_array = np.array(mzs)
    ims = np.full((len(mzs), img_shape[1], img_shape[0]), np.nan)
    for i in prange(len(coordinates)):
        (x, y, z_) = coordinates[i]
        spec_mzs, spec_ints = spectra[i]
        indices = _bisect_spectrum_multi(spec_mzs, mzs_array, np.array(tolerances))
        values = np.zeros(len(indices))
        for j, index in enumerate(indices):
            if len(spec_ints[index]) > 0:
                values[j] = np.max(spec_ints[index])
        ims[:, y - 1, x - 1] = values
    return ims


@njit
def _bisect_spectrum_multi(
    spectrum_mzs: npt.NDArray, mz_values: npt.NDArray, tolerances: npt.NDArray
):
    """
    Given a spectrum, an array of mz values, and a list of tolerances,
    return a list with for each mz an array that contains the indices of spectrum_mz
    that are within tolerance of the requested mz value.
    """
    ix_l = np.searchsorted(spectrum_mzs, mz_values - tolerances, "left")
    ix_u = np.searchsorted(spectrum_mzs, mz_values + tolerances, "right")

    # outside of right range
    r_out_range = ix_l >= len(spectrum_mzs)
    ix_l[r_out_range] = len(spectrum_mzs)
    ix_u[r_out_range] = len(spectrum_mzs) + 1

    # outside of left range
    l_out_range = ix_u < 1
    ix_l[l_out_range] = len(spectrum_mzs)
    ix_u[l_out_range] = len(spectrum_mzs) + 1

    index = [np.arange(s, e) for s, e in zip(ix_l, ix_u)]

    return index


def get_average_spectrum(p: ImzMLParser, bin_size: float) -> npt.NDArray:
    """
    Calculate average mass spectrum on a subset of a 1000 random spectra
    """
    num_spectra = min(1000, len(p.spectra))
    spectra = sample(p.spectra, num_spectra)
    return get_average_spectrum_numba(spectra=np.hstack(spectra), bin_size=bin_size)


def get_average_spectrum_numba(
    spectra: npt.NDArray, bin_size: float, threshold: int = 200
) -> npt.NDArray:
    """
    This function processes a 2D numpy array of spectra data, where each spectrum consists of
    x (wavelength or frequency) and y (intensity) values. The spectra are binned to compute
    an average spectrum.

    Parameters:
    spectra (npt.NDArray): NDarray hstack containing NDarray spectra
    bin_size (float): The size of each bin for averaging the spectrum.
    threshold (int, optional): A threshold value below which y values are set to zero.

    Returns:
    npt.NDArray: 2D numpy array with average spectrum
    """
    # Combine all x and y values into single numpy arrays
    all_x, all_y = np.split(spectra, [1], axis=0)
    all_x = all_x.flatten()
    all_y = all_y.flatten()
    all_y[all_y < threshold] = 0

    # Get the minimum and maximum x values to define bins
    min_x: float = np.min(all_x)
    max_x: float = np.max(all_x)

    # Define bins
    bins = np.arange(min_x, max_x + bin_size, bin_size, dtype=np.float64)
    bin_indices = np.digitize(all_x, bins) - 1

    # Initialize the array for bin means and counts
    bin_means = np.zeros(len(bins), dtype=np.float64)
    bin_counts = np.zeros(len(bins), dtype=np.int32)

    # Use np.add.at for accumulating y values and counts
    np.add.at(bin_means, bin_indices, all_y)
    np.add.at(bin_counts, bin_indices, 1)

    # Avoid division by zero
    nonzero_bins = bin_counts > 0
    bin_means[nonzero_bins] /= bin_counts[nonzero_bins]
    result = remove_extra_zeroes(np.vstack((bins, bin_means)))
    return result


def remove_extra_zeroes(spectra: npt.NDArray) -> npt.NDArray:
    """
    Remove datapoints where the intensty is zero but only if there is
    a non zero datapoint before or after the point.
    """
    size = spectra.shape[1]
    # Identify positions of non-zero elements
    non_zero_positions = np.nonzero(spectra[1, :])[0]

    # Create a mask for zeroes that are adjacent to non-zero elements
    mask = np.zeros_like(spectra[1, :], dtype=bool)

    # Mark non-zero positions
    mask[non_zero_positions] = True

    # Mark zeroes adjacent to non-zero elements
    for pos in non_zero_positions:
        if pos > 0:
            mask[pos - 1] = True
        if pos < size - 1:
            mask[pos + 1] = True

    # Apply the mask to the array
    mz = spectra[0, mask]
    intensity = spectra[1, mask]
    return np.array([mz, intensity])
