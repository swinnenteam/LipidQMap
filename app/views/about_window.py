from PySide6.QtWidgets import QWidget

from app.generated.MsiAboutDialog_ui import Ui_Dialog


class AboutWindow(QWidget, Ui_Dialog):
    """
    About window
    """

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.button_close.clicked.connect(self.close_window)

    def close_window(self) -> None:
        self.close()
