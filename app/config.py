"""
according to principles described:
https://tech.preferred.jp/en/blog/working-with-configuration-in-python/
"""

import os
import sys

import toml
from pydantic import BaseModel, Field


def get_bundle_dir() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore # pylint: disable=W0212
    else:
        return str(os.path.dirname(__file__))


config_paths = {
    "DATABASE_DIR": os.path.join(get_bundle_dir(), "database"),
    "USER_CONFIG_FILE": os.path.join(get_bundle_dir(), "config.toml"),
    "STYLE_FILE": os.path.join(get_bundle_dir(), "style.css"),
    "LOG_FILE": os.path.join(get_bundle_dir(), "log.txt"),
}


class DatabaseSettings(BaseModel):
    """
    Class for validation of the configuration file
    """

    last_used_database: str = Field(default="")


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

    minimum_pixels: int = Field(default=100)
    minimum_intensity: int = Field(default=1000)


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


config = Config()
