import sys
from typing import NoReturn

from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from app import __appname__, __desktopid__, __version__
from app.config import Config, config_paths
from app.database import load_database
from app.logger import UncaughtHook
from app.views.main_window import MainWindow


def main() -> NoReturn:
    """Instantiate program loading and start the main program."""
    # create the application
    app = QApplication(sys.argv)
    app.setApplicationVersion(__version__)
    app.setApplicationName(__appname__)
    app.setDesktopFileName(__desktopid__)

    # create main window
    window = MainWindow()
    window.setWindowTitle(__appname__)

    # Global error handling and logging
    _ = UncaughtHook()

    # setup stylesheet
    apply_stylesheet(app, theme="dark_teal.xml")

    # load database
    window.database = load_database(config_paths["DATABASE_FILE"])
    window.init_table()

    # Load configuration
    window.config = Config()
    window.resize(1800, 1000)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
