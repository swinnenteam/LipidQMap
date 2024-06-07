import os
from enum import Enum

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from matplotlib import colormaps, transforms
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from mpl_toolkits.axes_grid1 import make_axes_locatable

from app.dataprocess import ImageType, SampleImageCollection

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
        canvas_type: ImageType,
        parent=None,
    ):
        self.ncols: int = 2
        self.ims: list = []  # hold references to matplotlib subplots
        self.fig = plt.figure()
        self.canvas_type = canvas_type
        super(MplCanvas, self).__init__(self.fig)

    def setup(self, num_samples: int) -> None:

        # find number of required rows
        nrows = num_samples // self.ncols + (num_samples % self.ncols > 0)
        self.fig.set_size_inches(20, 6 * nrows)
        self.ims = []
        cmap = colormaps.get_cmap("viridis")
        blank_image = np.full([300, 500], np.nan)
        blank_image = np.random.random((300, 500))
        fg_color = "white"

        for sample_idx in range(num_samples):
            ax = plt.subplot(nrows, self.ncols, sample_idx + 1)
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

    def update_figure(self, samples: dict[str, SampleImageCollection], species_id: str) -> None:

        for i, (key, image_collection) in enumerate(samples.items()):
            image = image_collection.get(self.canvas_type, species_id)
            if image is None:
                x, y = image_collection.shape
                image = np.full([x, y], np.nan)
            self.ims[i].set_data(image)
            self.ims[i].autoscale()
            self.ims[i].set_clim(0, None)
            self.fig.axes[i * 2].set_title(key, color="white")

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
    ax.set_title(label=species, size=24)
    # image = np.rot90(image)
    img = ax.imshow(image, interpolation="gaussian", origin="lower")
    # ax.invert_yaxis()
    cbar = plt.colorbar(img, cax=cax)
    cbar.set_label(label="pmol / mm²", size=18)
    cbar.ax.tick_params(labelsize=18)
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
    # matplotlib bug workaround, equivalent to setting origin to upper in imsave
    result = np.ascontiguousarray(result[::-1])
    plt.imsave(fname=f"{full_path}_1to1_pixel.png", arr=result, format="png", origin="upper")
    plt.clf()
