import sys
from typing import NoReturn

from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from app import __appname__, __desktopid__, __version__
from app.config import config_paths
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
    apply_stylesheet(
        app,
        theme="dark_teal.xml",
        css_file=str(config_paths["STYLE_FILE"]),
        extra={
            "density_scale": "-1",
        },
    )

    window.resize(1800, 1000)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
