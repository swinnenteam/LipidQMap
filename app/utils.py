from PySide6.QtCore import QAbstractTableModel, QEvent, Qt
from PySide6.QtWidgets import QItemDelegate


class PandasModelEditable(QAbstractTableModel):

    def __init__(self, data, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = data
        self.checkableColumns = [2]
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

    def get_checked(self, row) -> bool:
        return self._data.iloc[row, 2]

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
                if isinstance(value, float):
                    value = "{:.5f}".format(value)
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


class BooleanDelegate(QItemDelegate):

    def __init__(self, *args, **kwargs):
        super(BooleanDelegate, self).__init__(*args, **kwargs)

    def paint(self, painter, option, index):
        value = index.data(Qt.CheckStateRole)
        self.drawCheck(painter, option, option.rect, value)
        self.drawFocus(painter, option, option.rect)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            value = bool(model.data(index, Qt.CheckStateRole))
            model.setData(index, not value)
            event.accept()
        return super(BooleanDelegate, self).editorEvent(event, model, option, index)
