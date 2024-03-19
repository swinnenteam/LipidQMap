from PySide6.QtWidgets import QMainWindow

from app import __appname__
from app.config import Config
from app.database import LipidDB
from app.generated.MsiMainWindow_ui import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Main window of the application
    """

    def __init__(self) -> None:
        super().__init__()
        self.database: LipidDB | None = None
        self.config: Config | None = None
        self.setupUi(self)
        self.connect_signals_slots()

    def connect_signals_slots(self) -> None:
        """Connect methods to signal slots."""

        self.action_open_imzml_file.triggered.connect(self.open_imzml_file)  # type: ignore

    def open_imzml_file(self) -> None:
        """Load an imzML file."""
        pass
