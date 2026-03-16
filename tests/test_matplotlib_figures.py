import matplotlib.pyplot as plt
import pytest
import numpy as np
from PIL import Image

from app.matplotlib_figures import (
    _add_export_image,
    _individual_export_figure_size,
    _panel_export_figure_size,
    _physical_image_aspect,
    save_individual_unfiltered_image,
)


def test_physical_image_aspect_respects_pixel_spacing() -> None:
    assert _physical_image_aspect((100, 100), None) == pytest.approx(1.0)
    assert _physical_image_aspect((100, 100), (1.0, 2.0)) == pytest.approx(2.0)
    assert _physical_image_aspect((80, 160), (2.0, 1.0)) == pytest.approx(0.25)


def test_individual_export_figure_size_tracks_non_square_pixels() -> None:
    square_size = _individual_export_figure_size((100, 100), None)
    tall_size = _individual_export_figure_size((100, 100), (1.0, 2.0))
    wide_size = _individual_export_figure_size((100, 100), (2.0, 1.0))

    assert tall_size[1] > tall_size[0]
    assert wide_size[0] > wide_size[1]
    assert tall_size[1] > square_size[1]
    assert wide_size[0] > square_size[0]


def test_panel_export_figure_size_grows_with_physical_aspect() -> None:
    square_size = _panel_export_figure_size([(100, 100)], [None], nrows=1, ncols=1)
    tall_size = _panel_export_figure_size([(100, 100)], [(1.0, 2.0)], nrows=1, ncols=1)

    assert tall_size[1] > square_size[1]


def test_add_export_image_keeps_non_square_data_bounds() -> None:
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)

    _add_export_image(
        ax,
        np.ones((100, 100), dtype=np.float32),
        interpolation="gaussian",
        pixel_size_um=(1.0, 2.0),
        cmap=plt.get_cmap("viridis"),
    )
    fig.canvas.draw()

    assert ax.get_xlim() == pytest.approx((0.0, 100.0))
    assert ax.get_ylim() == pytest.approx((0.0, 100.0))
    assert ax.get_aspect() == pytest.approx(2.0)

    plt.close(fig)


def test_save_individual_unfiltered_image_writes_tiff_metadata(tmp_path) -> None:
    save_individual_unfiltered_image(
        species_id="PC 34:1 [M+H]+",
        image=np.array([[1.0, np.nan], [2.0, 3.0]], dtype=np.float32),
        path=str(tmp_path),
        pixel_size_um=(50.0, 100.0),
    )

    written = tmp_path / "PC 34_1 [M+H]+_1to1_pixel.tiff"
    assert written.exists()

    with Image.open(written) as exported:
        assert exported.format == "TIFF"
        assert exported.size == (2, 2)
        assert exported.tag_v2.get(296) == 3
        assert exported.tag_v2.get(282) == pytest.approx(200.0)
        assert exported.tag_v2.get(283) == pytest.approx(100.0)
        description = exported.tag_v2.get(270)
        assert "pixel_size_um_x=50.000000" in description
        assert "pixel_size_um_y=100.000000" in description
