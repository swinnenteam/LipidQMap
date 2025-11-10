import os
import platform
import subprocess

from PySide6.QtCore import QAbstractTableModel, QEvent, Qt
from PySide6.QtWidgets import QItemDelegate


class PandasModelEditable(QAbstractTableModel):
    """
    A Qt model that adapts a pandas DataFrame for use in a QTableView,
    with support for checkable columns.

    Attributes:
        _data (pandas.DataFrame): The data source for the model.
        checkableColumns (list[int]): List of column indices that are checkable.
        boolean_delegate (BooleanDelegate): Delegate for handling boolean values.
    """

    def __init__(self, data, parent=None):
        """
        Initialize the model with a pandas DataFrame.

        Args:
            data (pandas.DataFrame): The data to be displayed and edited.
            parent: The parent object (default is None).
        """
        QAbstractTableModel.__init__(self, parent)
        self._data = data
        self.checkableColumns = {2}
        self.boolean_delegate = BooleanDelegate()

    def setColumnCheckable(self, column, checkable=True):
        if checkable:
            self.checkableColumns.add(column)
        else:
            self.checkableColumns.discard(column)
        self.dataChanged.emit(self.index(0, column), self.index(self.rowCount() - 1, column))

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def get_is_checked(self, row) -> bool:
        return self._data.iloc[row, 2]

    def get_checked_list(self) -> list[str]:
        df = self._data[self._data["Export"]]
        return df.index.tolist()

    def get_all_ids(self) -> list[str]:
        """Return all species IDs regardless of export checkbox."""
        return self._data.index.tolist()

    def data(self, index, role: int = Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.CheckStateRole and index.column() in self.checkableColumns:
                value = self._data.iloc[index.row(), index.column()]
                return Qt.CheckState.Checked if value else Qt.CheckState.Unchecked
            if index.column() not in self.checkableColumns and role in (
                Qt.ItemDataRole.DisplayRole,
                Qt.ItemDataRole.EditRole,
            ):
                value = self._data.iloc[index.row(), index.column()]
                # if isinstance(value, float):
                if index.column() == 1:
                    id = self._data.iloc[index.row(), 0]
                    if not ("]+" in id or "]-" in id):
                        value = ""
                    else:
                        value = "{:.5f}".format(value)
                else:
                    value = str(value)
                    if "]+" in value or "]-" in value:
                        value = "     " + value
                return value

        return None

    def setData(self, index, value, role: int = Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.CheckStateRole and index.column() in self.checkableColumns:
            self._data.iloc[index.row(), index.column()] = value == Qt.CheckState.Checked
            self.dataChanged.emit(index, index)
            return True
        if value is not None and role == Qt.ItemDataRole.EditRole:
            self._data.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section, orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._data.columns[section]
        if orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return self._data.index[section]
        return None

    def flags(self, index):
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() in self.checkableColumns:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags


class BooleanDelegate(QItemDelegate):
    """
    A delegate that handles the display and editing of boolean values in a model.
    """

    def __init__(self, *args, **kwargs):
        super(BooleanDelegate, self).__init__(*args, **kwargs)

    def paint(self, painter, option, index):
        value = index.data(Qt.ItemDataRole.CheckStateRole)
        self.drawCheck(painter, option, option.rect, value)
        self.drawFocus(painter, option, option.rect)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease:
            is_checked = model.data(index, Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked
            model.setData(index, not is_checked)
            event.accept()
        return super(BooleanDelegate, self).editorEvent(event, model, option, index)


def open_folder(path: str) -> None:
    """
    Open a folder in Finder (macOS) or Explorer (Windows).
    Falls back to xdg-open on Linux.
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        subprocess.run(["open", path], check=False)
    elif system == "Windows":
        # Use explorer — note backslashes are required
        norm_path = os.path.normpath(path)
        subprocess.run(["explorer", norm_path], check=False)
    else:  # Linux / other Unixes
        subprocess.run(["xdg-open", path], check=False)
