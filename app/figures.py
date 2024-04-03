import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from matplotlib import colormaps
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from mpl_toolkits.axes_grid1 import make_axes_locatable

from app.dataprocess import SampleImageCollection

plt.set_loglevel(level="warning")
plt.rcParams.update(
    {
        "figure.facecolor": (0.0, 0.0, 0.0, 0),
        "axes.facecolor": (0.0, 0.0, 0.0, 0),
        "savefig.facecolor": (0.0, 0.0, 0.0, 0),
    }
)


class MplCanvas(FigureCanvasQTAgg):

    def __init__(
        self,
        parent=None,
    ):

        self.fig, self.axes = plt.subplots(1, 1, figsize=(10, 6))
        self.axes.set_axis_off()
        super(MplCanvas, self).__init__(self.fig)

    def setup(self) -> None:

        cmap = colormaps.get_cmap("viridis")
        blank_image = np.full([300, 500], np.nan)
        fg_color = "white"

        # Extracted ion image
        self.ax1 = self.fig.add_subplot(2, 2, 1)
        self.im1 = self.ax1.imshow(
            blank_image, origin="lower", interpolation="nearest", cmap=cmap, vmin=0
        )
        divider = make_axes_locatable(self.ax1)
        cax = divider.append_axes("right", size="3%", pad=0.2)
        cb1 = plt.colorbar(self.im1, ax=self.ax1, cax=cax)

        # Extracted ion image, isotope corrected
        self.ax2 = self.fig.add_subplot(2, 2, 2)
        self.im2 = self.ax2.imshow(
            blank_image, origin="lower", interpolation="nearest", cmap=cmap, vmin=0
        )
        divider = make_axes_locatable(self.ax2)
        cax = divider.append_axes("right", size="3%", pad=0.2)
        cb2 = plt.colorbar(self.im2, ax=self.ax2, cax=cax)

        # Extracted ion image, isotope corrected and quantified
        self.ax3 = self.fig.add_subplot(2, 2, 3)
        self.im3 = self.ax3.imshow(
            blank_image, origin="lower", interpolation="nearest", cmap=cmap, vmin=0
        )
        divider = make_axes_locatable(self.ax3)
        cax = divider.append_axes("right", size="3%", pad=0.2)
        cb3 = plt.colorbar(self.im3, ax=self.ax3, cax=cax)

        self.ax1.set_axis_off()
        self.ax2.set_axis_off()
        self.ax3.set_axis_off()
        # self.axes[1, 1].set_axis_off()

        # set colorbar colors
        cb1.ax.yaxis.set_tick_params(color=fg_color)
        cb1.outline.set_edgecolor(fg_color)  # type: ignore [operator]
        plt.setp(plt.getp(cb1.ax.axes, "yticklabels"), color=fg_color)
        cb2.ax.yaxis.set_tick_params(color=fg_color)
        cb2.outline.set_edgecolor(fg_color)  # type: ignore [operator]
        plt.setp(plt.getp(cb2.ax.axes, "yticklabels"), color=fg_color)
        cb3.set_label("todo: unit of quant", color=fg_color)
        cb3.ax.yaxis.set_tick_params(color=fg_color)
        cb3.outline.set_edgecolor(fg_color)  # type: ignore [operator]
        plt.setp(plt.getp(cb3.ax.axes, "yticklabels"), color=fg_color)

        self.fig.subplots_adjust(
            left=0.05, right=0.95, bottom=0.05, top=0.95, wspace=0.2, hspace=0.2
        )
        # super(MplCanvas, self).__init__(self.fig)

    def update_figure(self, image_collection: SampleImageCollection, species_id: str) -> None:
        self.ax1.set_title(f"{species_id}", color="white")
        self.ax2.set_title(f"{species_id} Isocor", color="white")
        self.ax3.set_title(f"{species_id} Quant", color="white")
        self.im1.set_data(image_collection.raw_filtered.get(species_id))
        self.im1.autoscale()
        self.im1.set_clim(0, None)
        self.im2.set_data(image_collection.isotope_filtered.get(species_id))
        self.im2.autoscale()
        self.im2.set_clim(0, None)
        if species_id in image_collection.quant_filtered:
            self.im3.set_data(image_collection.quant_filtered.get(species_id))
        else:
            x, y = image_collection.raw_filtered[species_id].shape
            self.im3.set_data(np.full([x, y], np.nan))
        self.im3.autoscale()
        self.im3.set_clim(0, None)
        self.flush_events()
        self.draw()


def save_sample_image_collection(species: str, image: npt.NDArray, path: str) -> None:
    "Save the SampleImageCollection to PNG files."

    # image with colorbar
    full_path = os.path.join(path, species.replace(":", "_"))
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_axes(rect=(0.0, 0.0, 1.0, 1.0), frameon=False, xticks=[], yticks=[])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    ax.set_title(species)
    img = ax.imshow(image, interpolation="gaussian", origin="lower")
    plt.colorbar(img, cax=cax)
    plt.savefig(full_path, bbox_inches="tight", pad_inches=0)

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
    result = result.copy(order="C")
    plt.imsave(fname=f"{full_path}_1to1_pixel.png", arr=result, format="png", origin="upper")
    plt.clf()
