"""
according to principles described:
https://tech.preferred.jp/en/blog/working-with-configuration-in-python/
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

import toml
from platformdirs import user_data_dir
from pydantic import BaseModel, Field

from app import __appauthor__, __appname__


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _bundle_root() -> Path:
    if _is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def resource_path(*segments: str) -> Path:
    base = _bundle_root()
    for c in (base / "Resources" / Path(*segments), base / Path(*segments)):
        if c.exists():
            return c
    return Path(__file__).resolve().parent / Path(*segments)


def user_root() -> Path:
    p = Path(user_data_dir(appname=__appname__, appauthor=__appauthor__))
    p.mkdir(parents=True, exist_ok=True)
    return p


def user_db_dir() -> Path:
    p = user_root() / "database"
    p.mkdir(parents=True, exist_ok=True)
    return p


SEED_DB_WHITELIST = [
    "MSI_database_basic_V1.2.xlsx",
    "MSI_database_extensive_V1.2.xlsx",
]

SEED_DB_PACKAGED_DIR = ("seed",)  # inside Resources/seed when bundled
SEED_DB_DEV_DIR = Path(__file__).resolve().parent / "database"  # app/database in dev


def _seed_source_dir() -> Path:
    return resource_path(*SEED_DB_PACKAGED_DIR) if _is_frozen() else SEED_DB_DEV_DIR


def ensure_user_database_dir() -> Path:
    """
    Ensure the user database dir exists and contains the whitelisted seed files.
    Copies only files from SEED_DB_WHITELIST that are found in the seed source dir.
    Does not overwrite existing files.
    """
    dest = user_db_dir()
    src_dir = _seed_source_dir()

    for name in SEED_DB_WHITELIST:
        src = src_dir / name
        dst = dest / name
        if src.exists() and not dst.exists():
            dst.write_bytes(src.read_bytes())

    return dest


# ---- public paths ----
config_paths = {
    "DATABASE_DIR": str(user_db_dir()),
    "USER_CONFIG_FILE": str(user_root() / "config.toml"),
    "LOG_FILE": str(user_root() / "log.txt"),
    "STYLE_FILE": str(resource_path("style.css")),
    "SEED_DATABASE_DIR": str(resource_path(*SEED_DB_PACKAGED_DIR)),
}


class DatabaseSettings(BaseModel):
    """
    Class for validation of the configuration file
    """

    last_used_database: str = Field(default="MSI_database_basic_V1.2")


class FilterSettings(BaseModel):
    """
    Class for validation of the configuration file
    """

    raw_image_winsorizing_percentile: float = Field(default=99.0)
    quant_image_winsorizing_percentile: float = Field(default=99.0)
    gaussian_filter: bool = Field(default=True)


class SelectionSettings(BaseModel):
    """
    Class for validation of the configuration file
    """

    selection_method: Literal["threshold", "feature"] = Field(default="feature")
    minimum_pixels: int = Field(default=100)
    minimum_intensity: int = Field(default=1000)
    feature_noise_sigma: float = Field(default=4.0)
    feature_minimum_pixels: int = Field(default=10)


class SaveSettings(BaseModel):
    """
    Class for validation of the configuration file
    """

    save_raw_images: bool = Field(default=True)
    save_iso_images: bool = Field(default=False)
    save_quant_images: bool = Field(default=True)
    save_individual_unfiltered: bool = Field(default=False)
    save_individual_filtered_scaled: bool = Field(default=True)
    save_panel_filtered_scaled: bool = Field(default=True)


class ScaleBarSettings(BaseModel):
    """Configuration options for the image scale bar."""

    enabled: bool = Field(default=True)
    auto: bool = Field(default=True)
    manual_length_um: int = Field(default=100)


class ProcessingSettings(BaseModel):
    """
    Class for validation of the configuration file
    """

    pos_mode: bool = Field(default=True)
    ppm: float = Field(default=15.0)
    bin_size: float = Field(default=5.0)
    db_isotope_correction: bool = Field(default=True)
    na_isotope_correction: bool = Field(default=True)
    online_calibration: bool = Field(default=True)
    pos_calibrant: float = Field(default=798.5410)
    neg_calibrant: float = Field(default=798.5410)
    calibration_ppm: float = Field(default=30.0)
    calibration_min_intensity: int = Field(default=10000)
    imputation: bool = Field(default=True)


class SprayerSettings(BaseModel):
    """
    Class for validation of the configuration file
    """

    x_left: int = Field(default=20)  # mm
    x_right: int = Field(default=40)  # mm
    y_bottom: int = Field(default=5)  # mm
    y_top: int = Field(default=17)  # mm
    margin: int = Field(default=5)  # mm
    total_used_volume_mL: float = Field(default=0.80)  # mL
    syringe_flow_mL_per_min: float = Field(default=0.06)  # mL/min
    drying_time_min: float = Field(default=0.5)  # min
    drying_cycles: int = Field(default=16)  # unitless
    initial_equilibration_min: float = Field(default=0.833)  # min
    stock_conc_mg_per_mL: float = Field(default=0.11)  # mg/mL
    working_dilution_factor: float = Field(default=3)  # unitless
    volume_working_stock_uL: float = Field(default=1000)  # uL
    final_mix_volume_mL: float = Field(default=8)  # mL
    molecular_weight_ug_per_umol: float = Field(default=504.690)  # µg/µmol


class Configuration(BaseModel):
    """
    Class used by Config for validation of the configuration file
    """

    filter_settings: FilterSettings = FilterSettings()
    processing_settings: ProcessingSettings = ProcessingSettings()
    selection_settings: SelectionSettings = SelectionSettings()
    database_settings: DatabaseSettings = DatabaseSettings()
    save_settings: SaveSettings = SaveSettings()
    scalebar_settings: ScaleBarSettings = ScaleBarSettings()
    sprayer_settings: SprayerSettings = SprayerSettings()
    debug: bool = Field(default=False)


class Config:
    """
    Loads configuration settings from a specified toml file.
    The settings are stored in self.settings, a Pydantic class
    Validation of the settings is enforced by Pydantic.
    Settings are accessed and modified by accessing the properties of self.settings
    the save() method has to be called after modifying the properties.
    """

    def __init__(self, path: str = config_paths["USER_CONFIG_FILE"]):
        """Initialize based on specified path to config.toml file"""
        self.path: str = path
        self.load()

    def load(self):
        """Open the specified config toml file and convert to Config DataClass."""
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf8") as file:
                toml.dump(Configuration().model_dump(), file)
        with open(self.path, encoding="utf8") as file:
            config_toml = toml.load(file)
        self.settings = Configuration.model_validate(config_toml)

    def save(self):
        """Save the Config Dataclass (self.settings) to the toml file"""
        if self.settings:
            with open(self.path, "w", encoding="utf8") as file:
                toml.dump(self.settings.model_dump(), file)
                return self


_config: Config | None = None


def set_config(c: Config) -> None:
    global _config
    _config = c


def get_config() -> Config:
    global _config
    if _config is None:
        ensure_user_database_dir()  # safe to call repeatedly
        _config = Config()
    return _config
