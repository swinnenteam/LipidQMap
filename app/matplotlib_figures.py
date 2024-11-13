import os
import re
from pathlib import Path

import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import pandas as pd
from matplotlib import colormaps
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from mpl_toolkits.axes_grid1 import make_axes_locatable
from PySide6.QtCore import Signal

from app.config import Config
from app.database import LipidSpecies
from app.dataprocess import ImageType, SampleCollection, SectionMsiImage

matplotlib.use("Qtagg")

plt.set_loglevel(level="warning")
plt.rcParams.update(
    {
        "figure.facecolor": (0.0, 0.0, 0.0, 0),
        "axes.facecolor": (0.0, 0.0, 0.0, 0),
        "savefig.facecolor": (0.0, 0.0, 0.0, 0),
    }
)

cyan = "#1de9b6"


class BarplotCanvas(FigureCanvasQTAgg):
    """
    A custom matplotlib canvas for displaying a barplot.

    Attributes:
        fig (matplotlib.figure.Figure): The figure object.
    """

    def __init__(self, parent=None) -> None:
        """
        Initialize the MplCanvas.
        """
        self.fig: matplotlib.figure.Figure = plt.figure(layout="constrained")
        self.ax = self.fig.add_subplot(111)
        self.species_ids: list[str]
        self.values: list[float]
        super(BarplotCanvas, self).__init__(self.fig)

    def setup(self) -> None:
        """
        Set up the figure configuration.
        """
        # self.ax = self.fig.add_subplot(111)
        self.ax.tick_params(axis="x", labelrotation=90)
        self.ax.set_ylabel("Average Intensity")
        self.ax.spines["bottom"].set_color("white")
        self.ax.spines["top"].set_color((0, 0, 0, 0))
        self.ax.spines["right"].set_color((0, 0, 0, 0))
        self.ax.spines["left"].set_color("white")
        self.ax.tick_params(axis="x", colors="white", labelsize=9)
        self.ax.tick_params(axis="y", colors="white", labelsize=9)
        self.ax.yaxis.label.set_color("white")
        self.ax.xaxis.label.set_color("white")

    def update_figure(
        self, sample: SectionMsiImage, species: list[LipidSpecies], image_type: ImageType
    ) -> None:
        """
        Update the figure with new image data.

        Args:
            sample: SectionMsiImage
            species: list[LipidSpecies]
            image_type: ImageType
        """
        adduct = species[0].adduct
        self.values = [
            sample.get_mean(image_type=image_type, species_id=s.id_adduct) for s in species
        ]
        self.species_ids = [s.id for s in species]
        self.ax.cla()
        self.ax.bar(self.species_ids, self.values, color=[cyan])
        self.ax.text(
            0.99,
            0.99,
            adduct,
            ha="right",
            va="top",
            fontdict={"color": "white", "size": 10},
            transform=self.ax.transAxes,
        )
        self.draw()

    def reset_canvas(self) -> None:
        """
        Reset the canvas by clearing and removing all axes.
        """
        self.ax.cla()

    def copy_to_clipboard(self) -> None:
        pd.DataFrame(data=self.values, index=self.species_ids).to_clipboard()


class MplCanvas(FigureCanvasQTAgg):
    """
    A custom matplotlib canvas for displaying multiple images in a grid.

    Attributes:
        ncols (int): Number of columns in the grid.
        ims (list): List of matplotlib subplot image objects.
        fig (matplotlib.figure.Figure): The figure object.
        canvas_type (ImageType): Type of the image to be displayed (Raw, Iso or Quant).
    """

    image_clicked = Signal(str)

    def __init__(self, canvas_type: ImageType, config: Config, parent=None):
        """
        Initialize the MplCanvas.

        Args:
            canvas_type (ImageType): The type of image to be displayed.
            parent: The parent widget.
        """
        self.canvas_type = canvas_type
        self.config = config
        self.ncols: int = 2
        self.ims: list = []
        self.fig: matplotlib.figure.Figure = plt.figure()
        super(MplCanvas, self).__init__(self.fig)
        self.mpl_connect("button_press_event", self.on_press)

    def on_press(self, event):
        if event.inaxes is not None:
            self.image_clicked.emit(event.inaxes.get_title())

    def setup(self, nrows: int, ncols: int, dimensions: list[tuple[int, int]]) -> None:
        """
        Set up the grid layout for displaying images.

        Args:
            nrows (int): Number of rows in the grid.
            ncols (int): Number of columns in the grid.
            nsamples (int): Number of samples to display.
            dimensions list[tuple[int,int]]: list of x and y dimensions of the images
        """

        self.ims = []
        cmap = colormaps.get_cmap("viridis")
        fg_color = "white"

        filter = "gaussian" if self.config.settings.filter_settings.gaussian_filter else "nearest"
        for sample_idx, (x, y) in enumerate(dimensions):
            ax = self.fig.add_subplot(nrows, ncols, sample_idx + 1)
            im = ax.imshow(
                np.full([x, y], np.nan),
                origin="lower",
                interpolation=filter,
                cmap=cmap,
                vmin=0,
                aspect="equal",
            )
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
        self,
        samples: SampleCollection,
        species_id: str,
        active_sample_id: str,
        global_scale: bool = True,
    ) -> None:
        """
        Update the figure with new image data.

        Args:
            samples SampleCollection: Container that holds all the SectionMsiImages of each sample.
            species_id (str): The species identifier.
            global_scale (bool): Whether to use a global scale for all images (default is True).
        """

        max_value: int | None
        if global_scale:
            max_value = samples.get_max_intensity(
                species_id=species_id, image_type=self.canvas_type
            )
        else:
            max_value = None
        filter = "gaussian" if self.config.settings.filter_settings.gaussian_filter else "nearest"
        for i, (key, image_collection) in enumerate(samples.items()):
            image = image_collection.get(self.canvas_type, species_id)
            x, y = image_collection.shape
            if image is None:
                image = np.full([x, y], np.nan)
            if i >= len(self.ims):
                return
            self.ims[i].set_data(image)
            self.ims[i].set_extent((0, y, 0, x))
            self.ims[i].autoscale()
            self.ims[i].set_interpolation(filter)
            self.ims[i].set_clim(vmin=0, vmax=max_value)
            color = "white"
            if key == active_sample_id:
                color = cyan
            self.fig.axes[i * 2].set_title(key, fontdict={"color": color, "size": 10})

        self.flush_events()
        self.draw()

    def set_active_image(self, image_id) -> None:
        for ax in self.fig.get_axes():
            if image_id == ax.get_title():
                ax.title.set_color(cyan)
            else:
                ax.title.set_color("white")
        self.flush_events()
        self.draw()

    def reset_canvas(self) -> None:
        """
        Reset the canvases by clearing and removing all axes.
        """
        for ax in self.fig.get_axes():
            ax.cla()
            ax.remove()


def save_individual_image(
    species_id: str, image: npt.NDArray, max_scale: int | None, path: str, image_type: ImageType
) -> None:
    """
    Save an interpolated image with color scalebar to a PNG file.

    Args:
        species (str): The species name.
        image (npt.NDArray): The image data array.
        max_scale: (int | None): the maximum value for the color scale
        path (str): The directory path to save the image.
        image_type (ImageType): Raw, Iso or Quant image
    """

    # image with colorbar
    full_path = os.path.join(path, re.sub(r"[\/\\?%*:|\"<>]", "_", species_id))
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_axes(rect=(0.0, 0.0, 1.0, 1.0), frameon=False, xticks=[], yticks=[])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    ax.set_title(label=species_id, size=24)
    img = ax.imshow(image, interpolation="gaussian", origin="lower")
    img.set_clim(vmin=0, vmax=max_scale)
    cbar = plt.colorbar(img, cax=cax)
    if image_type == ImageType.quant:
        cbar.set_label(label="pmol / mm²", size=18)
    else:
        cbar.set_label(label="Intensity", size=18)
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
    lut = (colmap.colors[..., 0:3] * 255).astype(np.uint8)  # type: ignore
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
    full_path = os.path.join(path, re.sub(r"[\/\\?%*:|\"<>]", "_", species_id))
    plt.imsave(fname=f"{full_path}_1to1_pixel.png", arr=result, format="png", origin="upper")
    plt.close()


def save_panel_image(
    samples: SampleCollection,
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
        is_none = []
        max_value: int | None
        if global_scale:
            max_value = samples.get_max_intensity(species_id=species_id, image_type=image_type)
        else:
            max_value = None
        for sample_idx, (sample_id, image_collection) in enumerate(samples.items()):
            image = image_collection.get(image_type=image_type, species_id=species_id)
            if image is not None:
                is_none.append(False)
            else:
                is_none.append(True)
                continue
            ax = fig.add_subplot(nrows, ncols, sample_idx + 1)
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
            ax.set(adjustable="datalim")
            ax.apply_aspect()

            if image_type == ImageType.quant:
                cb.set_label("pmol / mm2")
        if all(is_none):
            continue
        fig.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95, wspace=0.2, hspace=0.2)
        full_path = os.path.join(base_path, re.sub(r"[\/\\?%*:|\"<>]", "_", species_id))
        plt.draw()
        fig.tight_layout()

        plt.savefig(
            fname=f"{full_path}.png", bbox_inches="tight", pad_inches=0, format="png", dpi=200
        )
        plt.close()


def save_image_collection(
    savepath: str,
    samples: SampleCollection,
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
                max_scale = samples.get_max_intensity(image_type=image_type, species_id=species)
                image = sample.get(image_type, species)
                if image is None:
                    continue
                if config.settings.save_settings.save_individual_filtered_scaled:
                    Path(path).mkdir(parents=True, exist_ok=True)
                    save_individual_image(
                        species_id=species,
                        image=image,
                        max_scale=max_scale,
                        path=path,
                        image_type=image_type,
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
