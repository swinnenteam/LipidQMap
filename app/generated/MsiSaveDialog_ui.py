# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiSaveDialog.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
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
    QHBoxLayout, QLabel, QLineEdit, QProgressBar,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_MsiSaveDialog(object):
    def setupUi(self, MsiSaveDialog):
        if not MsiSaveDialog.objectName():
            MsiSaveDialog.setObjectName(u"MsiSaveDialog")
        MsiSaveDialog.resize(607, 223)
        MsiSaveDialog.setMinimumSize(QSize(0, 0))
        self.verticalLayout_2 = QVBoxLayout(MsiSaveDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_select_folder = QLabel(MsiSaveDialog)
        self.label_select_folder.setObjectName(u"label_select_folder")

        self.horizontalLayout_3.addWidget(self.label_select_folder)

        self.line_edit_save_folder = QLineEdit(MsiSaveDialog)
        self.line_edit_save_folder.setObjectName(u"line_edit_save_folder")
        self.line_edit_save_folder.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.line_edit_save_folder)

        self.button_choose_save_folder = QPushButton(MsiSaveDialog)
        self.button_choose_save_folder.setObjectName(u"button_choose_save_folder")

        self.horizontalLayout_3.addWidget(self.button_choose_save_folder)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.groupBox = QGroupBox(MsiSaveDialog)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setMinimumSize(QSize(0, 0))
        self.verticalLayout_3 = QVBoxLayout(self.groupBox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.check_box_save_raw = QCheckBox(self.groupBox)
        self.check_box_save_raw.setObjectName(u"check_box_save_raw")
        self.check_box_save_raw.setChecked(True)

        self.verticalLayout_3.addWidget(self.check_box_save_raw)

        self.check_box_save_iso = QCheckBox(self.groupBox)
        self.check_box_save_iso.setObjectName(u"check_box_save_iso")

        self.verticalLayout_3.addWidget(self.check_box_save_iso)

        self.check_box_save_quant = QCheckBox(self.groupBox)
        self.check_box_save_quant.setObjectName(u"check_box_save_quant")
        self.check_box_save_quant.setChecked(True)

        self.verticalLayout_3.addWidget(self.check_box_save_quant)


        self.horizontalLayout_4.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(MsiSaveDialog)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setMinimumSize(QSize(0, 0))
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.check_box_save_individual = QCheckBox(self.groupBox_2)
        self.check_box_save_individual.setObjectName(u"check_box_save_individual")

        self.verticalLayout_4.addWidget(self.check_box_save_individual)

        self.check_box_save_filtered = QCheckBox(self.groupBox_2)
        self.check_box_save_filtered.setObjectName(u"check_box_save_filtered")
        self.check_box_save_filtered.setChecked(True)

        self.verticalLayout_4.addWidget(self.check_box_save_filtered)

        self.check_box_save_multi = QCheckBox(self.groupBox_2)
        self.check_box_save_multi.setObjectName(u"check_box_save_multi")
        self.check_box_save_multi.setChecked(True)

        self.verticalLayout_4.addWidget(self.check_box_save_multi)


        self.horizontalLayout_4.addWidget(self.groupBox_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.label = QLabel(MsiSaveDialog)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)

        self.verticalLayout_2.addWidget(self.label)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.progress_bar_save_images = QProgressBar(MsiSaveDialog)
        self.progress_bar_save_images.setObjectName(u"progress_bar_save_images")
        self.progress_bar_save_images.setValue(0)

        self.horizontalLayout_2.addWidget(self.progress_bar_save_images)

        self.button_cancel = QPushButton(MsiSaveDialog)
        self.button_cancel.setObjectName(u"button_cancel")

        self.horizontalLayout_2.addWidget(self.button_cancel)

        self.button_save = QPushButton(MsiSaveDialog)
        self.button_save.setObjectName(u"button_save")

        self.horizontalLayout_2.addWidget(self.button_save)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.retranslateUi(MsiSaveDialog)

        QMetaObject.connectSlotsByName(MsiSaveDialog)
    # setupUi

    def retranslateUi(self, MsiSaveDialog):
        MsiSaveDialog.setWindowTitle(QCoreApplication.translate("MsiSaveDialog", u"Save files", None))
        self.label_select_folder.setText(QCoreApplication.translate("MsiSaveDialog", u"Save in Folder:", None))
        self.button_choose_save_folder.setText(QCoreApplication.translate("MsiSaveDialog", u"Select Folder", None))
        self.groupBox.setTitle(QCoreApplication.translate("MsiSaveDialog", u"Images to save", None))
        self.check_box_save_raw.setText(QCoreApplication.translate("MsiSaveDialog", u"Raw images", None))
        self.check_box_save_iso.setText(QCoreApplication.translate("MsiSaveDialog", u"Isotope corrected images", None))
        self.check_box_save_quant.setText(QCoreApplication.translate("MsiSaveDialog", u"Quantitative images", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MsiSaveDialog", u"Image saving options", None))
        self.check_box_save_individual.setText(QCoreApplication.translate("MsiSaveDialog", u"Save individual unfiltered 1:1 pixel images", None))
        self.check_box_save_filtered.setText(QCoreApplication.translate("MsiSaveDialog", u"Save individual scaled and filtered images", None))
        self.check_box_save_multi.setText(QCoreApplication.translate("MsiSaveDialog", u"Save images as one panel, scaled and filtered", None))
        self.label.setText(QCoreApplication.translate("MsiSaveDialog", u"Note: saving the images may take several minutes and the program may appear unresponsive.", None))
        self.button_cancel.setText(QCoreApplication.translate("MsiSaveDialog", u"Cancel", None))
        self.button_save.setText(QCoreApplication.translate("MsiSaveDialog", u"Save", None))
    # retranslateUi

