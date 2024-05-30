"""
according to principles described:
https://tech.preferred.jp/en/blog/working-with-configuration-in-python/
"""

import os
import sys
from pathlib import Path

import toml
from pydantic import BaseModel, Field

if getattr(sys, "frozen", False):
    bundle_dir = os.path.dirname(sys.executable)  # type: ignore # pylint: disable=W0212
else:
    bundle_dir = str(os.path.dirname(__file__))

config_paths = {
    "DATABASE_DIR": os.path.join(bundle_dir, "database"),
    "USER_CONFIG_FILE": os.path.join(bundle_dir, "config.toml"),
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

    raw_image_winsorizing_percentile: int = Field(default=99)
    quant_image_winsorizing_percentile: int = Field(default=99)


class ProcessingSettings(BaseModel):
    """
    Class for validation of the configuration file
    """

    ppm: float = Field(default=15.0)
    m2_isotope_correction: bool = Field(default=True)
    na_isotope_correction: bool = Field(default=True)
    online_calibration: bool = Field(default=True)
    pos_calibrant: float = Field(default=798.5410)
    neg_calibrant: float = Field(default=798.5410)
    calibration_ppm: float = Field(default=30.0)
    calibration_max_intensity: int = Field(default=10000)


class Configuration(BaseModel):
    """
    Class used by Config for validation of the configuration file
    """

    filter_settings: FilterSettings = FilterSettings()
    processing_settings: ProcessingSettings = ProcessingSettings()
    database_settings: DatabaseSettings = DatabaseSettings()


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
