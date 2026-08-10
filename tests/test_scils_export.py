from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd

from app.scils_export import (
    _fit_coordinate_transform,
    _measurement_name_key,
    _prepare_value_sampler,
    _region_spots_for_sample,
    _select_spot_frame,
)


def _make_section(
    coords: np.ndarray,
    *,
    spot_ids: np.ndarray | None = None,
    stage_coords: np.ndarray | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        coordinates=coords,
        shape=(2, 2),
        spot_ids=spot_ids,
        stage_coordinates=stage_coords,
    )


def test_select_spot_frame_prefers_matching_measurement_by_coordinates() -> None:
    coords = np.array(
        [
            [1, 1, 0],
            [2, 1, 0],
            [1, 2, 0],
            [2, 2, 0],
        ],
        dtype=np.int32,
    )
    section = _make_section(coords)
    df = pd.DataFrame(
        {
            "spot_id": [1, 2, 3, 4, 5, 6, 7, 8],
            "x": [10, 11, 10, 11, 1, 2, 1, 2],
            "y": [10, 10, 11, 11, 1, 1, 2, 2],
            "measurement": ["A", "A", "A", "A", "B", "B", "B", "B"],
        }
    )

    frame = _select_spot_frame(df, section)

    assert frame["spot_id"].tolist() == [5, 6, 7, 8]


def test_select_spot_frame_prefers_spot_id_match_over_coordinate_match() -> None:
    coords = np.array(
        [
            [1, 1, 0],
            [2, 1, 0],
            [1, 2, 0],
            [2, 2, 0],
        ],
        dtype=np.int32,
    )
    section = _make_section(coords, spot_ids=np.array([5, 6, 7, 8], dtype=np.int64))
    df = pd.DataFrame(
        {
            "spot_id": [1, 2, 3, 4, 5, 6, 7, 8],
            "x": [1, 2, 1, 2, 1, 2, 1, 2],
            "y": [1, 1, 2, 2, 1, 1, 2, 2],
            "measurement": ["A", "A", "A", "A", "B", "B", "B", "B"],
        }
    )

    frame = _select_spot_frame(df, section)

    assert frame["spot_id"].tolist() == [5, 6, 7, 8]


def test_select_spot_frame_uses_stage_coordinates_when_available() -> None:
    pixel_coords = np.array(
        [
            [1, 1, 0],
            [2, 1, 0],
            [1, 2, 0],
            [2, 2, 0],
        ],
        dtype=np.int32,
    )
    stage_coords = np.array(
        [
            [-100, -50, 0],
            [-80, -50, 0],
            [-100, -30, 0],
            [-80, -30, 0],
        ],
        dtype=np.float64,
    )
    section = _make_section(pixel_coords, stage_coords=stage_coords)
    df = pd.DataFrame(
        {
            "spot_id": [1, 2, 3, 4, 5, 6, 7, 8],
            "x": [10, 11, 10, 11, -100, -80, -100, -80],
            "y": [10, 10, 11, 11, -50, -50, -30, -30],
            "measurement": ["A", "A", "A", "A", "B", "B", "B", "B"],
        }
    )

    frame = _select_spot_frame(df, section)

    assert frame["spot_id"].tolist() == [5, 6, 7, 8]


def test_select_spot_frame_falls_back_to_best_coordinate_match() -> None:
    coords = np.array(
        [
            [1, 1, 0],
            [2, 1, 0],
            [1, 2, 0],
            [2, 2, 0],
        ],
        dtype=np.int32,
    )
    section = _make_section(coords)
    df = pd.DataFrame(
        {
            "spot_id": [1, 2, 3, 4, 5, 6, 7, 8],
            "x": [50, 60, 50, 60, 11, 12, 11, 12],
            "y": [50, 50, 60, 60, 11, 11, 12, 12],
            "measurement": [
                "Preferred",
                "Preferred",
                "Preferred",
                "Preferred",
                "Other",
                "Other",
                "Other",
                "Other",
            ],
        }
    )

    frame = _select_spot_frame(
        df,
        section,
        preferred_sample_label="Preferred",
    )

    assert frame["spot_id"].tolist() == [5, 6, 7, 8]


def test_prepare_value_sampler_uses_spot_ids_when_matching() -> None:
    frame = pd.DataFrame(
        {
            "spot_id": [101, 102],
            "x": [1, 2],
            "y": [1, 1],
        }
    )
    coords = np.array([[1, 1, 0], [2, 1, 0]], dtype=np.int32)
    section = SimpleNamespace(
        coordinates=coords,
        _spot_index_lookup={101: 0, 102: 1},
    )
    sampler = _prepare_value_sampler(frame, section)
    image = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)

    np.testing.assert_array_equal(sampler(image), np.array([1.0, 2.0], dtype=np.float32))


def test_prepare_value_sampler_falls_back_when_spot_ids_missing() -> None:
    frame = pd.DataFrame(
        {
            "spot_id": [101, 999],
            "x": [1, 2],
            "y": [1, 2],
        }
    )
    coords = np.array([[1, 1, 0], [2, 2, 0]], dtype=np.int32)
    section = SimpleNamespace(
        coordinates=coords,
        _spot_index_lookup={101: 0},
    )
    sampler = _prepare_value_sampler(frame, section)
    image = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)

    np.testing.assert_array_equal(sampler(image), np.array([1.0, 4.0], dtype=np.float32))


def test_prepare_value_sampler_applies_coordinate_transform() -> None:
    pixels = np.array(
        [
            [1, 1, 0],
            [2, 1, 0],
            [1, 2, 0],
            [2, 2, 0],
        ],
        dtype=np.int32,
    )
    section = SimpleNamespace(
        coordinates=pixels,
        shape=(2, 2),
        _spot_index_lookup=None,
    )
    frame = pd.DataFrame(
        {
            "spot_id": [10, 11, 12, 13],
            "x": pixels[:, 0] * 10 + 5,
            "y": pixels[:, 1] * 20 - 3,
        }
    )
    transform = _fit_coordinate_transform(frame, section)
    assert transform is not None

    sampler = _prepare_value_sampler(frame, section, coord_transform=transform)
    image = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)

    np.testing.assert_array_equal(
        sampler(image),
        np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32),
    )


def test_prepare_value_sampler_prefers_transform_over_coincidental_spot_ids() -> None:
    frame = pd.DataFrame(
        {
            "spot_id": [0, 1],
            "x": [1, 2],
            "y": [1, 1],
        }
    )
    section = SimpleNamespace(
        coordinates=np.array([[2, 1, 0], [1, 1, 0]], dtype=np.int32),
        shape=(1, 2),
        _spot_index_lookup={0: 0, 1: 1},
    )
    identity_transform = (
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
    )

    sampler = _prepare_value_sampler(
        frame,
        section,
        coord_transform=identity_transform,
    )
    image = np.array([[10.0, 20.0]], dtype=np.float32)

    np.testing.assert_array_equal(
        sampler(image),
        np.array([10.0, 20.0], dtype=np.float32),
    )


def test_region_spots_for_sample_matches_normalized_measurement_name() -> None:
    expected_spots = {
        "spot_id": (10, 11),
        "raster": (4, 4),
        "x": np.array([1, 2]),
        "y": np.array([1, 1]),
        "z": np.array([0, 0]),
    }
    root = SimpleNamespace(id="Regions", name="Regions", spots={"spot_id": range(20)})
    match = SimpleNamespace(
        id="measurement-id",
        name="Regions/20260428_NEG_NOR_19N",
        spots=expected_spots,
    )
    root.get_all_regions = lambda: [root, match]
    dataset = SimpleNamespace(
        get_region_tree=lambda: root,
        get_region_spots=lambda _region_id: {"spot_id": range(20)},
    )
    section = _make_section(np.array([[1, 1, 0], [2, 1, 0]], dtype=np.int32))

    result = _region_spots_for_sample(
        dataset,
        section,
        "20260428_neg_nor_019n",
    )

    assert result is expected_spots
    assert _measurement_name_key("20260428_neg_nor_019n") == _measurement_name_key(
        "Regions/20260428_NEG_NOR_19N"
    )


def test_coordinate_transform_handles_cropped_spots_and_reversed_stage_y() -> None:
    pixels = np.array(
        [
            [1, 1, 0],
            [2, 1, 0],
            [1, 2, 0],
            [2, 2, 0],
            [1, 3, 0],
        ],
        dtype=np.int32,
    )
    stage = np.column_stack(
        (
            pixels[:, 0] * 10.0,
            100.0 - pixels[:, 1] * 10.0,
            np.zeros(len(pixels)),
        )
    )
    section = SimpleNamespace(
        coordinates=pixels,
        stage_coordinates=stage,
        shape=(3, 2),
        _spot_index_lookup=None,
    )
    # SCiLS has cropped one spot and translated the measurement in the
    # combined dataset. Its y axis retains the physical-stage direction.
    frame = pd.DataFrame(
        {
            "spot_id": [100, 101, 102, 103],
            "x": [1010.0, 1020.0, 1010.0, 1010.0],
            "y": [2090.0, 2090.0, 2080.0, 2070.0],
        }
    )

    transform = _fit_coordinate_transform(frame, section)
    assert transform is not None
    sampler = _prepare_value_sampler(frame, section, coord_transform=transform)
    image = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], dtype=np.float32)

    np.testing.assert_array_equal(
        sampler(image),
        np.array([1.0, 2.0, 3.0, 5.0], dtype=np.float32),
    )
