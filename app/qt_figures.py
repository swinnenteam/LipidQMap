import numpy as np
import numpy.typing as npt
from PySide6 import QtCharts, QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolTip

from app.config import Config
from app.dataprocess import ppm_to_tolerance

cyan = "#1de9b6"


def _safe_axis_upper(value: float | None) -> float:
    """Return a strictly positive finite axis maximum for chart display."""
    if value is None or not np.isfinite(value) or value <= 0:
        return 1.0
    return float(value)


class SpectrumPlot(QtCharts.QChart):
    def __init__(self) -> None:
        super().__init__()
        self.plot_data: npt.NDArray | None = None
        self.line_series = QtCharts.QLineSeries()
        self.target_series = QtCharts.QLineSeries()
        self.low_limit_series = QtCharts.QLineSeries()
        self.high_limit_series = QtCharts.QLineSeries()
        self.area_series_top = QtCharts.QLineSeries()
        self.area_series = QtCharts.QAreaSeries(self.area_series_top)

        self.addSeries(self.line_series)
        self.addSeries(self.low_limit_series)
        self.addSeries(self.target_series)
        self.addSeries(self.high_limit_series)
        self.addSeries(self.area_series_top)
        self.addSeries(self.area_series)
        self.line_series.hovered.connect(self.display_plot_value)
        self.setup_layout()

    def setup_layout(self) -> None:

        white = QtGui.QColor("white")
        orange = QtGui.QColor(255, 165, 0, 150)
        orange_transparant = QtGui.QColor(255, 165, 0, 12)
        transparent = QtGui.QColor("transparent")

        # Create a QValueAxis for the x-axis and set the tick count
        self.axis_x = QtCharts.QValueAxis()
        self.axis_x.setTickCount(10)  # Set the tick count to 10
        self.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.target_series.attachAxis(self.axis_x)
        self.low_limit_series.attachAxis(self.axis_x)
        self.high_limit_series.attachAxis(self.axis_x)
        self.area_series_top.attachAxis(self.axis_x)
        self.area_series.attachAxis(self.axis_x)
        self.line_series.attachAxis(self.axis_x)
        self.axis_x.setGridLineVisible(False)
        self.axis_x.setLabelsColor(white)
        self.axis_x.setLinePenColor(white)

        # Create a QValueAxis for the y-axis
        self.axis_y = QtCharts.QValueAxis()
        self.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)
        self.target_series.attachAxis(self.axis_y)
        self.low_limit_series.attachAxis(self.axis_y)
        self.high_limit_series.attachAxis(self.axis_y)
        self.area_series_top.attachAxis(self.axis_y)
        self.area_series.attachAxis(self.axis_y)
        self.line_series.attachAxis(self.axis_y)
        self.axis_y.setGridLineVisible(False)
        self.axis_y.setLabelsColor(white)
        self.axis_y.setLinePenColor(white)

        pen1 = self.line_series.pen()
        pen1.setWidth(1)
        pen1.setColor(QtGui.QColor(cyan))
        self.line_series.setPen(pen1)
        pen2 = self.target_series.pen()
        pen2.setWidth(1)
        pen2.setColor(orange)
        self.target_series.setPen(pen2)
        pen3 = self.low_limit_series.pen()
        pen3.setWidth(1)
        pen3.setDashPattern([4, 8])
        pen3.setColor(orange)
        self.low_limit_series.setPen(pen3)
        self.high_limit_series.setPen(pen3)
        pen4 = self.area_series_top.pen()
        pen4.setColor(transparent)
        self.area_series_top.setPen(pen4)
        self.area_series.setBorderColor(transparent)
        self.area_series.setColor(orange_transparant)

        self.setBackgroundBrush(transparent)
        self.legend().setVisible(False)
        self.layout().setContentsMargins(0, 0, 0, 0)

    @staticmethod
    def display_plot_value(point, state) -> None:
        pos = QtGui.QCursor.pos()
        if state:
            tooltip_text = f"m/z: {round(point.x(), 4)}, Intensity: {round(point.y(), 0)}"
            QToolTip.showText(pos, tooltip_text, msecShowTime=99999)

    def update_figure(self, data: npt.NDArray, x_max: float, y_max: float) -> None:
        self.plot_data = data
        self.line_series.clear()
        self.target_series.clear()
        self.low_limit_series.clear()
        self.high_limit_series.clear()
        self.area_series_top.clear()
        if data.size == 0 or data.shape[1] == 0:
            self.axis_x.setRange(0, 1)
            self.axis_y.setRange(0, 1)
            return
        self.line_series.replaceNp(data[0, :], data[1, :])
        self.axis_x.setRange(0, max(1.0, x_max))
        self.axis_y.setRange(0, _safe_axis_upper(y_max))

    def update_target(self, target: float, width: float) -> None:
        if self.plot_data is None or self.plot_data.size == 0 or self.plot_data.shape[1] == 0:
            return
        x_axis_min = target - 0.2
        x_axis_max = target + 0.2
        y_axis_max = self.get_y_max(x_axis_min, x_axis_max)
        max_y_value = _safe_axis_upper(np.max(self.plot_data[1, :]))

        self.target_series.clear()
        self.low_limit_series.clear()
        self.high_limit_series.clear()
        self.area_series_top.clear()
        self.low_limit_series.replaceNp(
            np.array([target - width / 2, target - width / 2]), np.array([0, max_y_value])
        )
        self.target_series.replaceNp(np.array([target, target]), np.array([0, max_y_value]))
        self.high_limit_series.replaceNp(
            np.array([target + width / 2, target + width / 2]), np.array([0, max_y_value])
        )
        self.area_series_top.replaceNp(
            np.array([target - width / 2, target + width / 2]), np.array([max_y_value, max_y_value])
        )

        self.axis_x.setRange(x_axis_min, x_axis_max)
        self.axis_y.setRange(0, _safe_axis_upper(y_axis_max))

    def autoscale_y_axis(self) -> None:
        x_min = self.axis_x.min()
        x_max = self.axis_x.max()
        if self.plot_data is None:
            return
        y_max = self.get_y_max(x_min, x_max)
        if y_max is None:
            return
        self.axis_y.setRange(0, y_max)

    def get_y_max(self, x_min: float, x_max: float) -> float | None:
        if self.plot_data is None or self.plot_data.size == 0 or self.plot_data.shape[1] == 0:
            return None
        min_index, max_index = np.searchsorted(self.plot_data[0, :], [x_min, x_max])
        y_values = self.plot_data[1, min_index:max_index]
        if y_values.size == 0:
            return None
        return _safe_axis_upper(np.max(y_values))


class SpectrumPlotView(QtCharts.QChartView):
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.plot = SpectrumPlot()
        self.plot_data: npt.NDArray | None = None
        self.setChart(self.plot)
        self._start_pos = None
        self._dragging = False
        QtGui.QPainter.RenderHint.Antialiasing
        self.setBackgroundBrush(QtGui.QColor(0, 0, 0, 0))
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.setRubberBand(QtCharts.QChartView.RubberBand.HorizontalRubberBand)

    def update_figure(self, data: npt.NDArray) -> None:
        self.plot_data = data
        if data.size == 0 or data.shape[1] == 0:
            self.x_min = 0.0
            self.x_max = 1.0
            self.y_max = 1.0
            self.plot.update_figure(data, self.x_max, self.y_max)
            self.update()
            return
        self.x_max = float(data[0, -1])
        self.x_min = float(data[0, 0])
        self.y_max = _safe_axis_upper(np.max(data[1, :]))
        self.plot.update_figure(data, self.x_max, self.y_max)
        self.update()

    def update_target(self, target_mz: float) -> None:
        ppm = self.config.settings.processing_settings.ppm
        width = ppm_to_tolerance(ppm, target_mz) * 2
        self.plot.update_target(target_mz, width)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.pos()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._start_pos:
            self._dragging = True
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self._start_pos:
            if self._dragging:
                # A drag event has taken place
                self.plot.autoscale_y_axis()
            self._start_pos = None
            self._dragging = False

    def mouseDoubleClickEvent(self, event):
        """
        Dubble click on the axis zoom out to max range
        """

        scene_pos = self.mapToScene(event.pos())
        plot_area = self.chart().plotArea()

        # Check if the click is on the x-axis labels
        if plot_area.contains(scene_pos.x(), plot_area.bottom()):
            self.plot.axis_x.setRange(self.x_min, self.x_max)
            self.plot.axis_y.setRange(0, self.y_max)
        # Check if the click is on the y-axis labels
        elif plot_area.contains(plot_area.left(), scene_pos.y()):
            self.plot.axis_y.setRange(0, self.y_max)
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event) -> None:
        """
        Zoom in/out on axis
        """

        if self.plot_data is None:
            return

        # Define zoom factor
        zoom_in_factor = 0.6
        zoom_out_factor = 1.8

        # Determine zoom direction
        scale = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor

        plot_area = self.chart().plotArea()
        scene_pos = self.mapToScene(event.position().toPoint())

        # on x-axis
        if plot_area.contains(scene_pos.x(), plot_area.bottom()):
            min = self.plot.axis_x.min()
            max = self.plot.axis_x.max()
            max_data = self.plot_data[0, -1]
            min_data = self.plot_data[0, 0]

            # Calculate new range
            position_value = self.plot.mapToValue(event.position()).x()
            new_max = np.min([position_value + (max - position_value) * scale, max_data])
            new_min = np.max([position_value - (position_value - min) * scale, min_data])

            self.plot.axis_x.setRange(new_min, new_max)

        # on y-axis
        elif plot_area.contains(plot_area.left(), scene_pos.y()):
            max = self.plot.axis_y.max()
            max_data = self.y_max
            new_max = np.min([max * scale, max_data])
            self.plot.axis_y.setRange(0, new_max)

        event.accept()
