# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiExportPickleDialog.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_MsiExportPickleDialog(object):
    def setupUi(self, MsiExportPickleDialog):
        if not MsiExportPickleDialog.objectName():
            MsiExportPickleDialog.setObjectName(u"MsiExportPickleDialog")
        MsiExportPickleDialog.resize(420, 270)
        self.verticalLayout = QVBoxLayout(MsiExportPickleDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_output = QLabel(MsiExportPickleDialog)
        self.label_output.setObjectName(u"label_output")

        self.verticalLayout.addWidget(self.label_output)

        self.layout_path = QHBoxLayout()
        self.layout_path.setObjectName(u"layout_path")
        self.line_edit_output = QLineEdit(MsiExportPickleDialog)
        self.line_edit_output.setObjectName(u"line_edit_output")

        self.layout_path.addWidget(self.line_edit_output)

        self.button_choose_file = QPushButton(MsiExportPickleDialog)
        self.button_choose_file.setObjectName(u"button_choose_file")

        self.layout_path.addWidget(self.button_choose_file)


        self.verticalLayout.addLayout(self.layout_path)

        self.group_box_image_type = QGroupBox(MsiExportPickleDialog)
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

        self.include_summed_checkbox = QCheckBox(MsiExportPickleDialog)
        self.include_summed_checkbox.setObjectName(u"include_summed_checkbox")

        self.verticalLayout.addWidget(self.include_summed_checkbox)

        self.selected_only_checkbox = QCheckBox(MsiExportPickleDialog)
        self.selected_only_checkbox.setObjectName(u"selected_only_checkbox")
        self.selected_only_checkbox.setChecked(True)

        self.verticalLayout.addWidget(self.selected_only_checkbox)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.layout_buttons = QHBoxLayout()
        self.layout_buttons.setObjectName(u"layout_buttons")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_buttons.addItem(self.horizontalSpacer)

        self.button_cancel = QPushButton(MsiExportPickleDialog)
        self.button_cancel.setObjectName(u"button_cancel")

        self.layout_buttons.addWidget(self.button_cancel)

        self.button_export = QPushButton(MsiExportPickleDialog)
        self.button_export.setObjectName(u"button_export")

        self.layout_buttons.addWidget(self.button_export)


        self.verticalLayout.addLayout(self.layout_buttons)


        self.retranslateUi(MsiExportPickleDialog)

        QMetaObject.connectSlotsByName(MsiExportPickleDialog)
    # setupUi

    def retranslateUi(self, MsiExportPickleDialog):
        MsiExportPickleDialog.setWindowTitle(QCoreApplication.translate("MsiExportPickleDialog", u"Export Python pickle", None))
        self.label_output.setText(QCoreApplication.translate("MsiExportPickleDialog", u"Output file:", None))
        self.button_choose_file.setText(QCoreApplication.translate("MsiExportPickleDialog", u"Select File", None))
        self.group_box_image_type.setTitle(QCoreApplication.translate("MsiExportPickleDialog", u"Images to export", None))
        self.radio_quant.setText(QCoreApplication.translate("MsiExportPickleDialog", u"Quantitative images", None))
        self.radio_iso.setText(QCoreApplication.translate("MsiExportPickleDialog", u"Isotope corrected images", None))
        self.radio_raw.setText(QCoreApplication.translate("MsiExportPickleDialog", u"Raw images", None))
#if QT_CONFIG(tooltip)
        self.include_summed_checkbox.setToolTip(QCoreApplication.translate("MsiExportPickleDialog", u"<html><head/><body><p>Include the neutral (summed adduct) ion images in the export. These images are generated by summing the different adducts that belong to the same species.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.include_summed_checkbox.setText(QCoreApplication.translate("MsiExportPickleDialog", u"Include ion images of summed adducts \u24d8", None))
        self.selected_only_checkbox.setText(QCoreApplication.translate("MsiExportPickleDialog", u"Only export selected (checked) features", None))
        self.button_cancel.setText(QCoreApplication.translate("MsiExportPickleDialog", u"Cancel", None))
        self.button_export.setText(QCoreApplication.translate("MsiExportPickleDialog", u"Export", None))
    # retranslateUi

