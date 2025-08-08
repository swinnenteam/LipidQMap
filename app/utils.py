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
        df = self._data[self._data["Export"] == True]
        return df.index.tolist()

    def data(self, index, role):
        if index.isValid():
            if role == Qt.CheckStateRole and index.column() in self.checkableColumns:
                value = self._data.iloc[index.row(), index.column()]
                return Qt.Checked if value else Qt.Unchecked
            if index.column() not in self.checkableColumns and role in (
                Qt.DisplayRole,
                Qt.EditRole,
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

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole and index.column() in self.checkableColumns:
            self._data.iloc[index.row(), index.column()] = value == Qt.Checked
            self.dataChanged.emit(index, index)
            return True
        if value is not None and role == Qt.EditRole:
            self._data.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[section]
        if orientation == Qt.Orientation.Vertical and role == Qt.DisplayRole:
            return self._data.index[section]
        return None

    def flags(self, index):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() in self.checkableColumns:
            flags |= Qt.ItemIsUserCheckable
        return flags


class BooleanDelegate(QItemDelegate):
    """
    A delegate that handles the display and editing of boolean values in a model.
    """

    def __init__(self, *args, **kwargs):
        super(BooleanDelegate, self).__init__(*args, **kwargs)

    def paint(self, painter, option, index):
        value = index.data(Qt.CheckStateRole)
        self.drawCheck(painter, option, option.rect, value)
        self.drawFocus(painter, option, option.rect)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            is_checked = model.data(index, Qt.CheckStateRole) == Qt.Checked
            model.setData(index, not is_checked)
            event.accept()
        return super(BooleanDelegate, self).editorEvent(event, model, option, index)
