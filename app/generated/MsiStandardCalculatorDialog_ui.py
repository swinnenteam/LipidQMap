# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiStandardCalculatorDialog.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(508, 525)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.database_label = QLabel(Dialog)
        self.database_label.setObjectName(u"database_label")

        self.horizontalLayout_2.addWidget(self.database_label)

        self.database_combo_box = QComboBox(Dialog)
        self.database_combo_box.setObjectName(u"database_combo_box")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.database_combo_box.sizePolicy().hasHeightForWidth())
        self.database_combo_box.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.database_combo_box)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.standards_list_view = QListWidget(Dialog)
        self.standards_list_view.setObjectName(u"standards_list_view")

        self.verticalLayout.addWidget(self.standards_list_view)

        self.quantity_line_edit = QLineEdit(Dialog)
        self.quantity_line_edit.setObjectName(u"quantity_line_edit")

        self.verticalLayout.addWidget(self.quantity_line_edit)

        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.save_button = QPushButton(Dialog)
        self.save_button.setObjectName(u"save_button")

        self.gridLayout_4.addWidget(self.save_button, 0, 2, 1, 1)

        self.cancel_button = QPushButton(Dialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout_4.addWidget(self.cancel_button, 0, 1, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_2, 0, 0, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_4)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Standard calculator", None))
        self.database_label.setText(QCoreApplication.translate("Dialog", u"Database:", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Standards:", None))
        self.save_button.setText(QCoreApplication.translate("Dialog", u"Save && Close", None))
        self.cancel_button.setText(QCoreApplication.translate("Dialog", u"Cancel", None))
    # retranslateUi

