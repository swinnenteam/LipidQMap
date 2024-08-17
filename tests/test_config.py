import os
from pathlib import Path

import pytest
import toml
from pydantic import ValidationError

from app.config import Config, Configuration


# Define a temporary directory for the test configurations
@pytest.fixture
def temp_config_dir():
    config_path = Path("tests/config.toml")
    yield config_path
    if config_path.exists():
        config_path.unlink()


def test_default_config_values(temp_config_dir):
    config = Config(path=str(temp_config_dir))

    assert config.settings.filter_settings.raw_image_winsorizing_percentile == 99
    assert config.settings.filter_settings.quant_image_winsorizing_percentile == 99

    assert config.settings.processing_settings.ppm == 15.0
    assert config.settings.processing_settings.m2_isotope_correction is True
    assert config.settings.processing_settings.na_isotope_correction is True
    assert config.settings.processing_settings.online_calibration is True
    assert config.settings.processing_settings.pos_calibrant == 798.5410
    assert config.settings.processing_settings.neg_calibrant == 798.5410
    assert config.settings.processing_settings.calibration_ppm == 30.0
    assert config.settings.processing_settings.calibration_min_intensity == 10000

    assert config.settings.database_settings.last_used_database == ""

    assert config.settings.save_settings.save_raw_images is True
    assert config.settings.save_settings.save_iso_images is False
    assert config.settings.save_settings.save_quant_images is True
    assert config.settings.save_settings.save_individual_unfiltered is False
    assert config.settings.save_settings.save_individual_filtered_scaled is True
    assert config.settings.save_settings.save_panel_filtered_scaled is True


def test_load_nonexistent_config_file(temp_config_dir):
    config_path = temp_config_dir
    assert not os.path.exists(config_path)

    config = Config(path=str(config_path))
    assert os.path.exists(config_path)

    with open(config_path, "r", encoding="utf8") as file:
        config_data = toml.load(file)
        assert Configuration.model_validate(config_data) is not None


def test_save_config_changes(temp_config_dir):
    config = Config(path=str(temp_config_dir))

    # Change a setting
    config.settings.filter_settings.raw_image_winsorizing_percentile = 95
    config.save()

    with open(temp_config_dir, "r", encoding="utf8") as file:
        config_data = toml.load(file)
        assert config_data["filter_settings"]["raw_image_winsorizing_percentile"] == 95


def test_invalid_config_loading(temp_config_dir):
    invalid_config_content = """
    [filter_settings]
    raw_image_winsorizing_percentile = "invalid_value"
    """

    with open(temp_config_dir, "w", encoding="utf8") as file:
        file.write(invalid_config_content)

    with pytest.raises(ValidationError):
        Config(path=str(temp_config_dir))


def test_partial_config_loading(temp_config_dir):
    partial_config_content = """
    [filter_settings]
    raw_image_winsorizing_percentile = 90
    """

    with open(temp_config_dir, "w", encoding="utf8") as file:
        file.write(partial_config_content)

    config = Config(path=str(temp_config_dir))

    assert config.settings.filter_settings.raw_image_winsorizing_percentile == 90
    assert config.settings.filter_settings.quant_image_winsorizing_percentile == 99

    assert config.settings.processing_settings.ppm == 15.0
    assert config.settings.save_settings.save_raw_images is True


def test_default_config_creation(temp_config_dir):
    config_path = temp_config_dir
    assert not os.path.exists(config_path)

    config = Config(path=str(config_path))
    assert os.path.exists(config_path)

    with open(config_path, "r", encoding="utf8") as file:
        config_data = toml.load(file)
        assert Configuration.model_validate(config_data) is not None
