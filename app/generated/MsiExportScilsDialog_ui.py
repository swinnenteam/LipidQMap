# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiExportScilsDialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QProgressBar, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_MsiExportScilsDialog(object):
    def setupUi(self, MsiExportScilsDialog):
        if not MsiExportScilsDialog.objectName():
            MsiExportScilsDialog.setObjectName(u"MsiExportScilsDialog")
        MsiExportScilsDialog.resize(366, 313)
        self.verticalLayout = QVBoxLayout(MsiExportScilsDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(MsiExportScilsDialog)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lineEdit = QLineEdit(MsiExportScilsDialog)
        self.lineEdit.setObjectName(u"lineEdit")

        self.horizontalLayout.addWidget(self.lineEdit)

        self.button_choose_file = QPushButton(MsiExportScilsDialog)
        self.button_choose_file.setObjectName(u"button_choose_file")

        self.horizontalLayout.addWidget(self.button_choose_file)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.label_scils_note = QLabel(MsiExportScilsDialog)
        self.label_scils_note.setObjectName(u"label_scils_note")
        self.label_scils_note.setWordWrap(True)

        self.verticalLayout.addWidget(self.label_scils_note)

        self.group_box_image_type = QGroupBox(MsiExportScilsDialog)
        self.group_box_image_type.setObjectName(u"group_box_image_type")
        self.verticalLayout_2 = QVBoxLayout(self.group_box_image_type)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.quant_checkbox = QCheckBox(self.group_box_image_type)
        self.quant_checkbox.setObjectName(u"quant_checkbox")
        self.quant_checkbox.setChecked(True)

        self.verticalLayout_2.addWidget(self.quant_checkbox)

        self.iso_checkbox = QCheckBox(self.group_box_image_type)
        self.iso_checkbox.setObjectName(u"iso_checkbox")

        self.verticalLayout_2.addWidget(self.iso_checkbox)

        self.raw_checkbox = QCheckBox(self.group_box_image_type)
        self.raw_checkbox.setObjectName(u"raw_checkbox")

        self.verticalLayout_2.addWidget(self.raw_checkbox)


        self.verticalLayout.addWidget(self.group_box_image_type)

        self.selected_only_checkbox = QCheckBox(MsiExportScilsDialog)
        self.selected_only_checkbox.setObjectName(u"selected_only_checkbox")
        self.selected_only_checkbox.setChecked(True)

        self.verticalLayout.addWidget(self.selected_only_checkbox)

        self.combo_box_adducts = QComboBox(MsiExportScilsDialog)
        self.combo_box_adducts.addItem("")
        self.combo_box_adducts.addItem("")
        self.combo_box_adducts.addItem("")
        self.combo_box_adducts.setObjectName(u"combo_box_adducts")

        self.verticalLayout.addWidget(self.combo_box_adducts)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scils_progressbar = QProgressBar(MsiExportScilsDialog)
        self.scils_progressbar.setObjectName(u"scils_progressbar")
        self.scils_progressbar.setValue(0)

        self.verticalLayout.addWidget(self.scils_progressbar)

        self.layout_buttons = QHBoxLayout()
        self.layout_buttons.setObjectName(u"layout_buttons")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_buttons.addItem(self.horizontalSpacer)

        self.button_cancel = QPushButton(MsiExportScilsDialog)
        self.button_cancel.setObjectName(u"button_cancel")

        self.layout_buttons.addWidget(self.button_cancel)

        self.button_export = QPushButton(MsiExportScilsDialog)
        self.button_export.setObjectName(u"button_export")

        self.layout_buttons.addWidget(self.button_export)


        self.verticalLayout.addLayout(self.layout_buttons)


        self.retranslateUi(MsiExportScilsDialog)

        QMetaObject.connectSlotsByName(MsiExportScilsDialog)
    # setupUi

    def retranslateUi(self, MsiExportScilsDialog):
        MsiExportScilsDialog.setWindowTitle(QCoreApplication.translate("MsiExportScilsDialog", u"Export to SCiLS", None))
        self.label.setText(QCoreApplication.translate("MsiExportScilsDialog", u"SCiLS Lab SLX file:", None))
        self.button_choose_file.setText(QCoreApplication.translate("MsiExportScilsDialog", u"Select File", None))
        self.label_scils_note.setText(QCoreApplication.translate("MsiExportScilsDialog", u"Note: SCiLS Lab must be open during export, but the target .slx file must not be open in SCiLS.", None))
        self.group_box_image_type.setTitle(QCoreApplication.translate("MsiExportScilsDialog", u"Images to export", None))
        self.quant_checkbox.setText(QCoreApplication.translate("MsiExportScilsDialog", u"Quantitative images", None))
        self.iso_checkbox.setText(QCoreApplication.translate("MsiExportScilsDialog", u"Isotope corrected images", None))
        self.raw_checkbox.setText(QCoreApplication.translate("MsiExportScilsDialog", u"Raw images", None))
        self.selected_only_checkbox.setText(QCoreApplication.translate("MsiExportScilsDialog", u"Only export selected (checked) features", None))
        self.combo_box_adducts.setItemText(0, QCoreApplication.translate("MsiExportScilsDialog", u"Adducts + summed adducts", None))
        self.combo_box_adducts.setItemText(1, QCoreApplication.translate("MsiExportScilsDialog", u"Adducts", None))
        self.combo_box_adducts.setItemText(2, QCoreApplication.translate("MsiExportScilsDialog", u"Summed", None))

        self.button_cancel.setText(QCoreApplication.translate("MsiExportScilsDialog", u"Cancel", None))
        self.button_export.setText(QCoreApplication.translate("MsiExportScilsDialog", u"Export", None))
    # retranslateUi

