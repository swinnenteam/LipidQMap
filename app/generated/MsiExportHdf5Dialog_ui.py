# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiExportHdf5Dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
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
from PySide6.QtWidgets import (QApplication, QDialog, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_MsiExportHdf5Dialog(object):
    def setupUi(self, MsiExportHdf5Dialog):
        if not MsiExportHdf5Dialog.objectName():
            MsiExportHdf5Dialog.setObjectName(u"MsiExportHdf5Dialog")
        MsiExportHdf5Dialog.resize(420, 240)
        self.verticalLayout = QVBoxLayout(MsiExportHdf5Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_output = QLabel(MsiExportHdf5Dialog)
        self.label_output.setObjectName(u"label_output")

        self.verticalLayout.addWidget(self.label_output)

        self.layout_path = QHBoxLayout()
        self.layout_path.setObjectName(u"layout_path")
        self.line_edit_output = QLineEdit(MsiExportHdf5Dialog)
        self.line_edit_output.setObjectName(u"line_edit_output")

        self.layout_path.addWidget(self.line_edit_output)

        self.button_choose_file = QPushButton(MsiExportHdf5Dialog)
        self.button_choose_file.setObjectName(u"button_choose_file")

        self.layout_path.addWidget(self.button_choose_file)


        self.verticalLayout.addLayout(self.layout_path)

        self.group_box_image_type = QGroupBox(MsiExportHdf5Dialog)
        self.group_box_image_type.setObjectName(u"group_box_image_type")
        self.verticalLayout_2 = QVBoxLayout(self.group_box_image_type)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.radio_quant = QRadioButton(self.group_box_image_type)
        self.radio_quant.setObjectName(u"radio_quant")
        self.radio_quant.setChecked(True)

        self.verticalLayout_2.addWidget(self.radio_quant)

        self.radio_iso = QRadioButton(self.group_box_image_type)
        self.radio_iso.setObjectName(u"radio_iso")

        self.verticalLayout_2.addWidget(self.radio_iso)

        self.radio_raw = QRadioButton(self.group_box_image_type)
        self.radio_raw.setObjectName(u"radio_raw")

        self.verticalLayout_2.addWidget(self.radio_raw)


        self.verticalLayout.addWidget(self.group_box_image_type)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.layout_buttons = QHBoxLayout()
        self.layout_buttons.setObjectName(u"layout_buttons")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_buttons.addItem(self.horizontalSpacer)

        self.button_cancel = QPushButton(MsiExportHdf5Dialog)
        self.button_cancel.setObjectName(u"button_cancel")

        self.layout_buttons.addWidget(self.button_cancel)

        self.button_export = QPushButton(MsiExportHdf5Dialog)
        self.button_export.setObjectName(u"button_export")

        self.layout_buttons.addWidget(self.button_export)


        self.verticalLayout.addLayout(self.layout_buttons)


        self.retranslateUi(MsiExportHdf5Dialog)

        QMetaObject.connectSlotsByName(MsiExportHdf5Dialog)
    # setupUi

    def retranslateUi(self, MsiExportHdf5Dialog):
        MsiExportHdf5Dialog.setWindowTitle(QCoreApplication.translate("MsiExportHdf5Dialog", u"Export Cardinal HDF5", None))
        self.label_output.setText(QCoreApplication.translate("MsiExportHdf5Dialog", u"Output file:", None))
        self.button_choose_file.setText(QCoreApplication.translate("MsiExportHdf5Dialog", u"Select File", None))
        self.group_box_image_type.setTitle(QCoreApplication.translate("MsiExportHdf5Dialog", u"Images to export", None))
        self.radio_quant.setText(QCoreApplication.translate("MsiExportHdf5Dialog", u"Quantitative images", None))
        self.radio_iso.setText(QCoreApplication.translate("MsiExportHdf5Dialog", u"Isotope corrected images", None))
        self.radio_raw.setText(QCoreApplication.translate("MsiExportHdf5Dialog", u"Raw images", None))
        self.button_cancel.setText(QCoreApplication.translate("MsiExportHdf5Dialog", u"Cancel", None))
        self.button_export.setText(QCoreApplication.translate("MsiExportHdf5Dialog", u"Export", None))
    # retranslateUi

