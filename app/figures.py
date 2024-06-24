import os
from pathlib import Path

import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from matplotlib import colormaps
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from mpl_toolkits.axes_grid1 import make_axes_locatable

from app.config import Config
from app.dataprocess import ImageType, SampleImageCollection

matplotlib.use("Qtagg")

plt.set_loglevel(level="warning")
plt.rcParams.update(
    {
        "figure.facecolor": (0.0, 0.0, 0.0, 0),
        "axes.facecolor": (0.0, 0.0, 0.0, 0),
        "savefig.facecolor": (0.0, 0.0, 0.0, 0),
    }
)


class MplCanvas(FigureCanvasQTAgg):
    """
    A custom matplotlib canvas for displaying multiple images in a grid.

    Attributes:
        ncols (int): Number of columns in the grid.
        ims (list): List of matplotlib subplot image objects.
        fig (matplotlib.figure.Figure): The figure object.
        canvas_type (ImageType): Type of the image to be displayed (Raw, Iso or Quant).
    """

    def __init__(self, canvas_type: ImageType, parent=None):
        """
        Initialize the MplCanvas.

        Args:
            canvas_type (ImageType): The type of image to be displayed.
            parent: The parent widget.
        """
        self.ncols: int = 2
        self.ims: list = []
        self.fig: matplotlib.figure.Figure = plt.figure()
        self.canvas_type = canvas_type
        super(MplCanvas, self).__init__(self.fig)

    def setup(self, nrows: int, ncols: int, nsamples: int) -> None:
        """
        Set up the grid layout for displaying images.

        Args:
            nrows (int): Number of rows in the grid.
            ncols (int): Number of columns in the grid.
            nsamples (int): Number of samples to display.
        """

        # self.fig.set_size_inches(20, 6 * nrows)
        self.ims = []
        cmap = colormaps.get_cmap("viridis")
        blank_image = np.full([300, 500], np.nan)
        fg_color = "white"

        for sample_idx in range(nsamples):
            ax = self.fig.add_subplot(nrows, ncols, sample_idx + 1)
            # interpolation nearest or gaussian
            im = ax.imshow(blank_image, origin="lower", interpolation="gaussian", cmap=cmap, vmin=0)
            self.ims.append(im)
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="3%", pad=0.2)
            cb = plt.colorbar(im, ax=ax, cax=cax)
            ax.set_axis_off()

            # set colorbar colors
            cb.ax.yaxis.set_tick_params(color=fg_color)
            cb.outline.set_edgecolor(fg_color)  # type: ignore [operator]
            plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color=fg_color)

            if self.canvas_type == ImageType.quant:
                cb.set_label("pmol / mm2", color=fg_color)

        self.fig.subplots_adjust(
            left=0.05, right=0.95, bottom=0.05, top=0.95, wspace=0.2, hspace=0.2
        )

    def update_figure(
        self, samples: dict[str, SampleImageCollection], species_id: str, global_scale: bool = True
    ) -> None:
        """
        Update the figure with new image data.

        Args:
            samples (dict[str, SampleImageCollection]): Dictionary of sample image collections.
            species_id (str): The species identifier.
            global_scale (bool): Whether to use a global scale for all images (default is True).
        """

        max_value: int | None
        if global_scale:
            max_value = get_max_from_image_collection(
                samples=samples, species_id=species_id, image_type=self.canvas_type
            )
        else:
            max_value = None

        for i, (key, image_collection) in enumerate(samples.items()):
            image = image_collection.get(self.canvas_type, species_id)
            if image is None:
                x, y = image_collection.shape
                image = np.full([x, y], np.nan)
            if i >= len(self.ims):
                return
            self.ims[i].set_data(image)
            self.ims[i].autoscale()
            self.ims[i].set_clim(vmin=0, vmax=max_value)
            self.fig.axes[i * 2].set_title(key, color="white")

        self.flush_events()
        self.draw()


def get_max_from_image_collection(
    samples: dict[str, SampleImageCollection],
    species_id: str,
    image_type: ImageType,
) -> int | None:
    max_value: int | None = 0
    for i, (key, image_collection) in enumerate(samples.items()):
        image = image_collection.get(image_type, species_id)
        image_max = np.nanmax(image) if image is not None else 0
        max_value = image_max if image_max > max_value else max_value
    max_value = None if max_value == 0 else max_value
    return max_value


def save_individual_image(
    species_id: str, image: npt.NDArray, max_scale: int | None, path: str
) -> None:
    """
    Save an interpolated image with color scalebar to a PNG file.

    Args:
        species (str): The species name.
        image (npt.NDArray): The image data array.
        max_scale: (int | None): the maximum value for the color scale
        path (str): The directory path to save the image.
    """

    # image with colorbar
    full_path = os.path.join(path, species_id.replace(":", "_"))
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_axes(rect=(0.0, 0.0, 1.0, 1.0), frameon=False, xticks=[], yticks=[])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    ax.set_title(label=species_id, size=24)
    # image = np.rot90(image)
    img = ax.imshow(image, interpolation="gaussian", origin="lower")
    img.set_clim(vmin=0, vmax=max_scale)
    # ax.invert_xaxis()
    cbar = plt.colorbar(img, cax=cax)
    cbar.set_label(label="pmol / mm²", size=18)
    cbar.ax.tick_params(labelsize=18)
    plt.savefig(full_path, bbox_inches="tight", pad_inches=0)
    plt.close()


def save_individual_unfiltered_image(species_id: str, image: npt.NDArray, path: str) -> None:
    """
    Save a 1 to 1 pixel representation of the image to a PNG file.

    Args:
        species (str): The species name.
        image (npt.NDArray): The image data array.
        path (str): The directory path to save the image.
    """

    # 1 to 1 pixel image
    image_no_nan = np.nan_to_num(x=image, nan=0, copy=True)
    colmap = plt.get_cmap("viridis", 256)
    lut = (colmap.colors[..., 0:3] * 255).astype(np.uint8)
    # to map the image to RGBA, scale to [0-255]
    rescaled = (
        (image_no_nan.astype(float) - image_no_nan.min())
        * 255
        / (image_no_nan.max() - image_no_nan.min())
    ).astype(np.uint8)
    result = np.zeros((*rescaled.shape, 3), dtype=np.uint8)
    mask = np.zeros((rescaled.shape), dtype=np.uint8)
    mask[~np.isnan(image)] = 255
    # Take entries from RGB LUT according to greyscale values in image
    result = np.take(lut, rescaled, axis=0, out=result)
    result = np.dstack([result, mask])
    # matplotlib bug workaround, equivalent to setting origin to upper in imsave
    result = np.ascontiguousarray(result[::-1])
    full_path = os.path.join(path, species_id.replace(":", "_"))
    plt.imsave(fname=f"{full_path}_1to1_pixel.png", arr=result, format="png", origin="upper")
    plt.close()


def save_panel_image(
    samples: dict[str, SampleImageCollection],
    global_scale: bool,
    path: str,
    nrows: int,
    ncols: int,
    image_type: ImageType,
    species_selection: list[str],
) -> None:
    """
    Save a matplotlib image panel to a PNG file.

    Args:
        species (str): The species name.
        image (matplotlib.figure.Figure): A matplotlib figure.
        path (str): The directory path to save the image.
    """
    base_path = os.path.join(path, image_type, "combined")
    Path(base_path).mkdir(parents=True, exist_ok=True)
    for species_id in species_selection:
        fig: matplotlib.figure.Figure = plt.figure(figsize=(6 * ncols, 4 * nrows))
        max_value: int | None
        if global_scale:
            max_value = get_max_from_image_collection(
                samples=samples, species_id=species_id, image_type=image_type
            )
        else:
            max_value = None
        for sample_idx, (sample_id, image_collection) in enumerate(samples.items()):
            ax = fig.add_subplot(nrows, ncols, sample_idx + 1)
            image = image_collection.get(image_type=image_type, species_id=species_id)
            if image is None:
                x, y = image_collection.shape
                image = np.full([x, y], np.nan)
            im = ax.imshow(
                image,
                origin="lower",
                interpolation="gaussian",
                cmap=colormaps.get_cmap("viridis"),
                vmin=0,
            )
            im.set_clim(vmin=0, vmax=max_value)

            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="3%", pad=0.2)
            ax.set_title(sample_id)
            cb = plt.colorbar(im, ax=ax, cax=cax)
            ax.set_axis_off()
            ax.set_aspect("auto")
            ax.apply_aspect()

            if image_type == ImageType.quant:
                cb.set_label("pmol / mm2")

        fig.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95, wspace=0.2, hspace=0.2)
        full_path = os.path.join(base_path, species_id.replace(":", "_"))
        plt.draw()
        fig.tight_layout()

        plt.savefig(
            fname=f"{full_path}.png", bbox_inches="tight", pad_inches=0, format="png", dpi=200
        )
        plt.close()


def save_image_collection(
    savepath: str,
    samples: dict[str, SampleImageCollection],
    species_selection: list[str],
    global_scale: bool,
    nrows: int,
    ncols: int,
    config: Config,
) -> None:
    """
    Save image collection.
    """
    # save raw images

    image_types = []
    if config.settings.save_settings.save_raw_images:
        image_types.append(ImageType.raw)
    if config.settings.save_settings.save_iso_images:
        image_types.append(ImageType.isotope)
    if config.settings.save_settings.save_quant_images:
        image_types.append(ImageType.quant)

    for image_type in image_types:
        for sample_name, sample in samples.items():
            path = os.path.join(savepath, image_type, sample_name)
            for species in species_selection:
                max_scale = get_max_from_image_collection(samples, species, image_type)
                image = sample.get(image_type, species)
                if image is None:
                    continue
                if config.settings.save_settings.save_individual_filtered_scaled:
                    Path(path).mkdir(parents=True, exist_ok=True)
                    save_individual_image(
                        species_id=species, image=image, max_scale=max_scale, path=path
                    )
                if config.settings.save_settings.save_individual_unfiltered:
                    Path(path).mkdir(parents=True, exist_ok=True)
                    save_individual_unfiltered_image(species_id=species, image=image, path=path)
        if config.settings.save_settings.save_panel_filtered_scaled:
            save_panel_image(
                samples=samples,
                path=savepath,
                global_scale=global_scale,
                nrows=nrows,
                ncols=ncols,
                image_type=image_type,
                species_selection=species_selection,
            )
    # progress_overall_callback.emit(100)
