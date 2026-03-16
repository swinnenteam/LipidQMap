import os
import re
import logging
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import pandas as pd
from PIL import Image, TiffImagePlugin
from matplotlib import colormaps
from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtCore import Signal
from matplotlib_scalebar.scalebar import ScaleBar

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
logger = logging.getLogger(__name__)


def _remove_scalebar(artist: Any | None) -> None:
    """Remove a previously attached scalebar artist if it exists."""
    if artist is None:
        return
    if hasattr(artist, "remove"):
        try:
            artist.remove()
        except ValueError:
            # already removed from the figure
            pass


def _attach_scale_bar(
    ax: Axes,
    pixel_size_um: tuple[float, float] | None,
    scale_length_um: int | None,
    color: str,
) -> Any | None:
    """Attach a scalebar to *ax* and return the created artist."""
    if pixel_size_um is None or scale_length_um is None:
        return None
    pixel_size_x = float(pixel_size_um[0])
    if pixel_size_x <= 0:
        return None

    scalebar = ScaleBar(
        dx=pixel_size_x,
        units="um",
        fixed_value=float(scale_length_um),
        fixed_units="um",
        color=color,
        box_alpha=0,
        location="lower right",
        scale_loc="bottom",
        label_loc="bottom",
        length_fraction=None,
    )
    scalebar.scale_formatter = lambda value, unit: f"{int(round(value))} {unit}"
    scalebar.set_zorder(5)
    ax.add_artist(scalebar)
    return scalebar


def _pixel_display_aspect(pixel_size_um: tuple[float, float] | None) -> float:
    """Return y/x display scaling based on physical pixel spacing."""
    if pixel_size_um is None:
        return 1.0
    pixel_size_x = float(pixel_size_um[0])
    pixel_size_y = float(pixel_size_um[1])
    if (
        pixel_size_x <= 0
        or pixel_size_y <= 0
        or not np.isfinite(pixel_size_x)
        or not np.isfinite(pixel_size_y)
    ):
        return 1.0
    ratio = pixel_size_y / pixel_size_x
    return ratio if np.isfinite(ratio) and ratio > 0 else 1.0


def _physical_image_aspect(
    image_shape: tuple[int, int], pixel_size_um: tuple[float, float] | None
) -> float:
    """Return the physical height/width aspect ratio for an image."""
    height_px, width_px = image_shape
    if height_px <= 0 or width_px <= 0:
        return 1.0
    physical_aspect = (height_px / width_px) * _pixel_display_aspect(pixel_size_um)
    return physical_aspect if np.isfinite(physical_aspect) and physical_aspect > 0 else 1.0


def _scaled_box_dimensions(
    box_aspect: float,
    *,
    target_area_in2: float,
    min_dim_in: float,
    max_dim_in: float,
) -> tuple[float, float]:
    """Return width/height in inches for a box with a given aspect."""
    safe_aspect = box_aspect if np.isfinite(box_aspect) and box_aspect > 0 else 1.0
    width_in = float(np.sqrt(target_area_in2 / safe_aspect))
    height_in = width_in * safe_aspect

    scale_up = max(min_dim_in / width_in, min_dim_in / height_in, 1.0)
    width_in *= scale_up
    height_in *= scale_up

    scale_down = min(max_dim_in / width_in, max_dim_in / height_in, 1.0)
    width_in *= scale_down
    height_in *= scale_down
    return width_in, height_in


def _individual_export_figure_size(
    image_shape: tuple[int, int], pixel_size_um: tuple[float, float] | None
) -> tuple[float, float]:
    """Return a figure size that keeps anisotropic images visually prominent."""
    image_width_in, image_height_in = _scaled_box_dimensions(
        _physical_image_aspect(image_shape, pixel_size_um),
        target_area_in2=36.0,
        min_dim_in=4.0,
        max_dim_in=10.0,
    )
    return image_width_in + 1.0, image_height_in + 0.8


def _panel_export_figure_size(
    image_shapes: list[tuple[int, int]],
    pixel_sizes_um: list[tuple[float, float] | None],
    nrows: int,
    ncols: int,
) -> tuple[float, float]:
    """Return a panel figure size derived from the most demanding sample aspect."""
    aspects = [
        _physical_image_aspect(image_shape, pixel_size_um)
        for image_shape, pixel_size_um in zip(image_shapes, pixel_sizes_um, strict=False)
    ]
    max_aspect = max(aspects, default=1.0)
    cell_width_in, cell_height_in = _scaled_box_dimensions(
        max_aspect,
        target_area_in2=14.0,
        min_dim_in=2.4,
        max_dim_in=5.0,
    )
    figure_width_in = ncols * (cell_width_in + 0.3) + 0.5
    figure_height_in = nrows * cell_height_in + 0.4
    return figure_width_in, figure_height_in


def _add_export_image(
    ax: Axes,
    image: npt.NDArray,
    *,
    interpolation: str,
    pixel_size_um: tuple[float, float] | None,
    cmap: Any,
) -> Any:
    """Render an image on an axis using the same aspect logic as the UI."""
    height_px, width_px = image.shape
    img = ax.imshow(image, origin="upper", interpolation=interpolation, cmap=cmap, vmin=0)
    img.set_extent((0, width_px, 0, height_px))
    ax.set_aspect(_pixel_display_aspect(pixel_size_um), adjustable="box")
    ax.set_xlim(0, width_px)
    ax.set_ylim(0, height_px)
    ax.margins(0)
    return img


def _tiff_resolution_metadata(
    pixel_size_um: tuple[float, float] | None,
) -> TiffImagePlugin.ImageFileDirectory_v2 | None:
    """Build TIFF metadata for physical pixel size if available."""
    if pixel_size_um is None:
        return None
    pixel_size_x, pixel_size_y = (float(pixel_size_um[0]), float(pixel_size_um[1]))
    if (
        pixel_size_x <= 0
        or pixel_size_y <= 0
        or not np.isfinite(pixel_size_x)
        or not np.isfinite(pixel_size_y)
    ):
        return None

    pixel_size_cm_x = pixel_size_x / 10000.0
    pixel_size_cm_y = pixel_size_y / 10000.0
    pixels_per_cm_x = 1.0 / pixel_size_cm_x
    pixels_per_cm_y = 1.0 / pixel_size_cm_y

    ifd = TiffImagePlugin.ImageFileDirectory_v2()
    ifd[270] = (
        f"LipidQMap 1:1 pixel export; pixel_size_um_x={pixel_size_x:.6f}; "
        f"pixel_size_um_y={pixel_size_y:.6f}"
    )
    ifd[282] = pixels_per_cm_x
    ifd[283] = pixels_per_cm_y
    ifd[296] = 3
    ifd[305] = "LipidQMap"
    return ifd


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
        self.scale_bars: list[Any | None] = []
        self.cbars: list[Any] = []
        self.fig: matplotlib.figure.Figure = plt.figure()
        super(MplCanvas, self).__init__(self.fig)
        self.mpl_connect("button_press_event", self.on_press)

    def on_press(self, event):
        if event.inaxes is not None:
            self.image_clicked.emit(event.inaxes.get_title())

    def setup(self, nrows: int, ncols: int, dimensions: list[tuple[int, int]]) -> None:
        self.ims = []
        self.scale_bars = []
        self.cbars = []
        nsamples = len(dimensions)
        if nsamples == 0:
            return
        ncols_eff = max(1, min(ncols, nsamples))
        nrows_eff = nsamples // ncols_eff + (nsamples % ncols_eff > 0)
        cmap = colormaps.get_cmap("viridis")
        fg_color = "white"

        filter = "gaussian" if self.config.settings.filter_settings.gaussian_filter else "nearest"

        col_widths = []
        for _ in range(ncols_eff):
            col_widths.append(20)
            col_widths.append(1)
        gs = self.fig.add_gridspec(
            nrows_eff,
            ncols_eff * 2,
            width_ratios=col_widths,
            left=0.01,
            right=0.94,
            bottom=0.01,
            top=0.93,
            wspace=0.04,
            hspace=0.15,
        )

        for sample_idx, (x, y) in enumerate(dimensions):
            row = sample_idx // ncols_eff
            col = sample_idx % ncols_eff
            ax = self.fig.add_subplot(gs[row, col * 2])
            cax_container = self.fig.add_subplot(gs[row, col * 2 + 1])
            cax_container.set_axis_off()
            cax = cax_container.inset_axes([0.0, 0.25, 1.0, 0.5])
            im = ax.imshow(
                np.full([x, y], np.nan),
                origin="upper",
                interpolation=filter,
                cmap=cmap,
                vmin=0,
                aspect="auto",
            )
            self.ims.append(im)
            self.scale_bars.append(None)
            cb = plt.colorbar(im, cax=cax)
            self.cbars.append(cb)
            ax.set_axis_off()

            # set colorbar colors
            cb.ax.yaxis.set_tick_params(color=fg_color)
            cb.outline.set_edgecolor(fg_color)  # type: ignore [operator]
            plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color=fg_color)
            cb.ax.patch.set_visible(False)
            cb.ax.tick_params(labelcolor=fg_color, labelsize=8)

            if self.canvas_type == ImageType.quant:
                cb.set_label("pmol / mm2", color=fg_color)

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
        logger.debug(
            "update_figure: species_id=%s max_value=%s canvas_type=%s",
            species_id,
            max_value,
            self.canvas_type,
        )
        filter = "gaussian" if self.config.settings.filter_settings.gaussian_filter else "nearest"
        scale_bar_length_um = samples.get_scalebar_length_um(self.config)
        for i, (key, image_collection) in enumerate(samples.items()):
            image = image_collection.get(self.canvas_type, species_id)
            x, y = image_collection.shape
            if image is None:
                image = np.full([x, y], np.nan)
            if i >= len(self.ims):
                return
            ax = self.ims[i].axes
            self.ims[i].set_data(image)
            self.ims[i].set_extent((0, y, 0, x))
            self.ims[i].set_interpolation(filter)
            has_data = np.isfinite(image).any() and np.nanmax(image) > 0
            if max_value is not None and max_value > 0:
                self.ims[i].set_clim(vmin=0, vmax=max_value)
            elif has_data:
                self.ims[i].set_clim(vmin=0, vmax=None)
                self.ims[i].autoscale()
            else:
                self.ims[i].set_clim(vmin=0, vmax=1)
            aspect = _pixel_display_aspect(image_collection.pixel_size_um)
            ax.set_aspect(aspect, adjustable="box")
            color = "white"
            if key == active_sample_id:
                color = cyan
            ax.set_title(key, fontdict={"color": color, "size": 10})

            if i < len(self.scale_bars):
                _remove_scalebar(self.scale_bars[i])
                self.scale_bars[i] = None
                if scale_bar_length_um is not None:
                    scalebar = _attach_scale_bar(
                        ax=ax,
                        pixel_size_um=image_collection.pixel_size_um,
                        scale_length_um=scale_bar_length_um,
                        color="white",
                    )
                    self.scale_bars[i] = scalebar

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
        self.scale_bars = []
        self.cbars = []


def save_individual_image(
    species_id: str,
    image: npt.NDArray,
    max_scale: int | None,
    path: str,
    image_type: ImageType,
    pixel_size_um: tuple[float, float] | None = None,
    scale_bar_length_um: int | None = None,
) -> None:
    """
    Save an interpolated image with color scalebar to a PNG file.

    Args:
        species (str): The species name.
        image (npt.NDArray): The image data array.
        max_scale: (int | None): the maximum value for the color scale
        path (str): The directory path to save the image.
        image_type (ImageType): Raw, Iso or Quant image
        pixel_size_um (tuple[float, float] | None): Pixel size metadata for scalebar placement.
        scale_bar_length_um (int | None): Shared scale bar length in micrometers.
    """

    # image with colorbar
    full_path = os.path.join(path, re.sub(r"[\/\\?%*:|\"<>]", "_", species_id))
    fig = plt.figure(
        figsize=_individual_export_figure_size(image.shape, pixel_size_um), layout="constrained"
    )
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 0.06])
    ax = fig.add_subplot(gs[0, 0])
    cax = fig.add_subplot(gs[0, 1])
    ax.set_title(label=species_id, size=20)
    img = _add_export_image(
        ax,
        image,
        interpolation="gaussian",
        pixel_size_um=pixel_size_um,
        cmap=colormaps.get_cmap("viridis"),
    )
    img.set_clim(vmin=0, vmax=max_scale)
    cbar = plt.colorbar(img, cax=cax)
    if image_type == ImageType.quant:
        cbar.set_label(label="pmol / mm²", size=14)
    else:
        cbar.set_label(label="Intensity", size=14)
    cbar.ax.tick_params(labelsize=12)
    ax.set_axis_off()
    _attach_scale_bar(
        ax=ax, pixel_size_um=pixel_size_um, scale_length_um=scale_bar_length_um, color="black"
    )
    fig.savefig(full_path, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def save_individual_unfiltered_image(
    species_id: str,
    image: npt.NDArray,
    path: str,
    pixel_size_um: tuple[float, float] | None = None,
) -> None:
    """
    Save a 1 to 1 pixel representation of the image to a PNG file.

    Args:
        species (str): The species name.
        image (npt.NDArray): The image data array.
        path (str): The directory path to save the image.
        pixel_size_um (tuple[float, float] | None): Pixel size metadata for TIFF export.
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
    save_kwargs: dict[str, Any] = {"format": "TIFF"}
    metadata = _tiff_resolution_metadata(pixel_size_um)
    if metadata is not None:
        save_kwargs["tiffinfo"] = metadata
    Image.fromarray(result, mode="RGBA").save(f"{full_path}_1to1_pixel.tiff", **save_kwargs)


def save_panel_image(
    samples: SampleCollection,
    global_scale: bool,
    path: str,
    nrows: int,
    ncols: int,
    image_type: ImageType,
    species_selection: list[str],
    scale_bar_length_um: int | None,
) -> None:
    """
    Save a matplotlib image panel to a PNG file.

    Args:
        species (str): The species name.
        image (matplotlib.figure.Figure): A matplotlib figure.
        path (str): The directory path to save the image.
        scale_bar_length_um (int | None): Shared scale bar length in micrometers.
    """
    base_path = os.path.join(path, image_type, "combined")
    Path(base_path).mkdir(parents=True, exist_ok=True)
    filter_name = "gaussian"
    cmap = colormaps.get_cmap("viridis")
    for species_id in species_selection:
        rendered_shapes: list[tuple[int, int]] = []
        rendered_pixel_sizes: list[tuple[float, float] | None] = []
        max_value: int | None
        if global_scale:
            max_value = samples.get_max_intensity(species_id=species_id, image_type=image_type)
        else:
            max_value = None

        for _, image_collection in samples.items():
            image = image_collection.get(image_type=image_type, species_id=species_id)
            if image is not None:
                rendered_shapes.append(image.shape)
                rendered_pixel_sizes.append(image_collection.pixel_size_um)

        if not rendered_shapes:
            continue

        fig = plt.figure(
            figsize=_panel_export_figure_size(
                rendered_shapes,
                rendered_pixel_sizes,
                nrows=nrows,
                ncols=ncols,
            ),
            layout="constrained",
        )
        gs = fig.add_gridspec(
            nrows,
            ncols * 2,
            width_ratios=[ratio for _ in range(ncols) for ratio in (1.0, 0.06)],
        )

        for sample_idx, (sample_id, image_collection) in enumerate(samples.items()):
            image = image_collection.get(image_type=image_type, species_id=species_id)
            if image is None:
                continue

            row = sample_idx // ncols
            col = sample_idx % ncols
            ax = fig.add_subplot(gs[row, col * 2])
            cax = fig.add_subplot(gs[row, col * 2 + 1])
            im = _add_export_image(
                ax,
                image,
                interpolation=filter_name,
                pixel_size_um=image_collection.pixel_size_um,
                cmap=cmap,
            )
            im.set_clim(vmin=0, vmax=max_value)

            ax.set_title(sample_id)
            cb = plt.colorbar(im, cax=cax)
            ax.set_axis_off()

            _attach_scale_bar(
                ax=ax,
                pixel_size_um=image_collection.pixel_size_um,
                scale_length_um=scale_bar_length_um,
                color="black",
            )

            if image_type == ImageType.quant:
                cb.set_label("pmol / mm2")

        full_path = os.path.join(base_path, re.sub(r"[\/\\?%*:|\"<>]", "_", species_id))
        fig.savefig(
            fname=f"{full_path}.png", bbox_inches="tight", pad_inches=0, format="png", dpi=200
        )
        plt.close(fig)


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

    scale_bar_length_um = samples.get_scalebar_length_um(config)

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
                        pixel_size_um=sample.pixel_size_um,
                        scale_bar_length_um=scale_bar_length_um,
                    )
                if config.settings.save_settings.save_individual_unfiltered:
                    Path(path).mkdir(parents=True, exist_ok=True)
                    save_individual_unfiltered_image(
                        species_id=species,
                        image=image,
                        path=path,
                        pixel_size_um=sample.pixel_size_um,
                    )
        if config.settings.save_settings.save_panel_filtered_scaled:
            save_panel_image(
                samples=samples,
                path=savepath,
                global_scale=global_scale,
                nrows=nrows,
                ncols=ncols,
                image_type=image_type,
                species_selection=species_selection,
                scale_bar_length_um=scale_bar_length_um,
            )
