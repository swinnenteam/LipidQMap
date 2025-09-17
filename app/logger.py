import logging
import sys
import traceback
from types import TracebackType
from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import config_paths, get_config


def _compute_log_level(debug_override: Optional[bool] = None) -> int:
    """Decide log level from override or config.settings.debug (defaults to ERROR)."""
    if debug_override is not None:
        return logging.DEBUG if debug_override else logging.ERROR
    try:
        cfg = get_config()
        return logging.DEBUG if getattr(cfg.settings, "debug", False) else logging.ERROR
    except Exception:
        return logging.ERROR


def setup_logging(debug_override: Optional[bool] = None) -> logging.Logger:
    """
    Configure the root logger once. Safe to call multiple times.
    """
    logger = logging.getLogger()  # root
    level = _compute_log_level(debug_override)
    logger.setLevel(level)

    if not getattr(logger, "_lipidqmap_handlers_installed", False):
        log_path = config_paths["LOG_FILE"]

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        stream_handler = logging.StreamHandler()

        fmt = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(fmt)
        stream_handler.setFormatter(fmt)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

        # Mark so we don’t add handlers again
        logger._lipidqmap_handlers_installed = True  # type: ignore[attr-defined]

    return logger


def show_exception_box(error: tuple[type, BaseException, TracebackType]) -> None:
    """
    Show a critical message box if a QApplication exists; else just log.
    """
    if QApplication.instance() is not None:
        errorbox = QMessageBox()
        errorbox.setIcon(QMessageBox.Icon.Critical)
        errorbox.setText(str(error[0].__name__))
        errorbox.setInformativeText(str(error[1]))
        errorbox.setDetailedText("".join(traceback.format_tb(error[2])))
        errorbox.exec_()
    else:
        logging.debug("No QApplication instance available.")


class UncaughtHook(QObject):
    """
    This object hooks error logging and an error messagebox to the interpreter,
    in case an unhandled exception is raised during runtime.
    """

    _exception_caught = Signal(object)

    def __init__(self, *args, **kwargs) -> None:
        super(UncaughtHook, self).__init__(*args, **kwargs)

        # this registers the exception_hook() function as hook with the Python interpreter
        sys.excepthook = self.exception_hook
        # threading.excepthook = self.exception_hook

        # connect signal to execute the message box function always on main thread
        self._exception_caught.connect(show_exception_box)

    def exception_hook(self, exc_type, exc_value, exc_traceback) -> None:
        """
        Function handling uncaught exceptions.
        It is triggered each time an uncaught exception occurs.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            # ignore keyboard interrupt to support console applications
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        else:
            exc_info = (exc_type, exc_value, exc_traceback)
            log_msg = "\n".join(
                [
                    "".join(traceback.format_tb(exc_traceback)),
                    f"{exc_type.__name__}: {exc_value}",
                ]
            )
            logging.critical("Uncaught exception:\n %s", log_msg, exc_info=exc_info)

            # trigger message box show
            self._exception_caught.emit(exc_info)


def install_qt_exception_hook() -> UncaughtHook:
    """
    Create and install the UncaughtHook. Returns the instance so you can keep a ref.
    """
    return UncaughtHook()
