from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    result
        2 objects returned from processing

    progress
        int indicating % progress

    """

    finished = Signal()
    result = Signal(object, object)
    progress_file = Signal(int)
    progress_overall = Signal(int)


class Worker(QRunnable):
    """
    Worker thread, handles a function that returns 2 results

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    """

    def __init__(self, function, *args, **kwargs) -> None:
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs["progress_file_callback"] = self.signals.progress_file
        self.kwargs["progress_overall_callback"] = self.signals.progress_overall

    @Slot()
    def run(self) -> None:
        """
        Initialise the runner function with passed args, kwargs.
        """

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result_1, result_2 = self.function(*self.args, **self.kwargs)
        except Exception as exc:  # pylint: disable=bare-except
            raise exc
        else:
            self.signals.result.emit(result_1, result_2)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done
