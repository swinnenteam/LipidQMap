from PySide6.QtCore import QAbstractTableModel, Qt


class PandasModelEditable(QAbstractTableModel):

    def __init__(self, data, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = data
        self.checkableColumns = [2]

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

    def get_checked(self, row) -> bool:
        return self._data.iloc[row, 2]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.CheckStateRole and index.column() in self.checkableColumns:
                value = self._data.iloc[index.row(), index.column()]
                return Qt.Checked if value else Qt.Unchecked
            elif index.column() not in self.checkableColumns and role in (
                Qt.DisplayRole,
                Qt.EditRole,
            ):
                value = self._data.iloc[index.row(), index.column()]
                if isinstance(value, float):
                    value = "{:.4f}".format(value)
                else:
                    value = str(value)
                return value

        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole and index.column() in self.checkableColumns:
            self._data.iloc[index.row(), index.column()] = bool(value)
            self.dataChanged.emit(index, index)
            return True
        if value is not None and role == Qt.EditRole:
            self._data.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[section]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return self._data.index[section]
        return None

    def flags(self, index):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() in self.checkableColumns:
            flags |= Qt.ItemIsUserCheckable
        return flags
