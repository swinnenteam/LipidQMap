# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiSettingsDialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QDoubleSpinBox,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(517, 267)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.groupBox_2 = QGroupBox(Dialog)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout_4 = QGridLayout(self.groupBox_2)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.spinbox_min_pixels = QSpinBox(self.groupBox_2)
        self.spinbox_min_pixels.setObjectName(u"spinbox_min_pixels")
        self.spinbox_min_pixels.setMaximum(10000000)
        self.spinbox_min_pixels.setSingleStep(100)
        self.spinbox_min_pixels.setValue(100)

        self.gridLayout_3.addWidget(self.spinbox_min_pixels, 0, 1, 1, 1)

        self.label_3 = QLabel(self.groupBox_2)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 1)

        self.label_4 = QLabel(self.groupBox_2)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_3.addWidget(self.label_4, 0, 2, 1, 1)

        self.spinbox_min_intensity = QSpinBox(self.groupBox_2)
        self.spinbox_min_intensity.setObjectName(u"spinbox_min_intensity")
        self.spinbox_min_intensity.setMaximum(10000000)
        self.spinbox_min_intensity.setSingleStep(100)
        self.spinbox_min_intensity.setValue(1000)

        self.gridLayout_3.addWidget(self.spinbox_min_intensity, 0, 3, 1, 1)


        self.gridLayout_4.addLayout(self.gridLayout_3, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.groupBox_2, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.button_cancel = QPushButton(Dialog)
        self.button_cancel.setObjectName(u"button_cancel")

        self.horizontalLayout.addWidget(self.button_cancel)

        self.button_save = QPushButton(Dialog)
        self.button_save.setObjectName(u"button_save")

        self.horizontalLayout.addWidget(self.button_save)


        self.gridLayout.addLayout(self.horizontalLayout, 3, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 2, 0, 1, 1)

        self.groupBox = QGroupBox(Dialog)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.check_box_gaussian_filter = QCheckBox(self.groupBox)
        self.check_box_gaussian_filter.setObjectName(u"check_box_gaussian_filter")

        self.gridLayout_2.addWidget(self.check_box_gaussian_filter, 0, 0, 1, 1)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFormAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.label)

        self.spinbox_winsor_quant = QDoubleSpinBox(self.groupBox)
        self.spinbox_winsor_quant.setObjectName(u"spinbox_winsor_quant")
        self.spinbox_winsor_quant.setDecimals(1)
        self.spinbox_winsor_quant.setValue(99.000000000000000)

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.spinbox_winsor_quant)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.label_2)

        self.spinbox_winsor_raw = QDoubleSpinBox(self.groupBox)
        self.spinbox_winsor_raw.setObjectName(u"spinbox_winsor_raw")
        self.spinbox_winsor_raw.setDecimals(1)
        self.spinbox_winsor_raw.setValue(99.000000000000000)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.spinbox_winsor_raw)


        self.gridLayout_2.addLayout(self.formLayout, 1, 0, 1, 2)


        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Settings", None))
#if QT_CONFIG(tooltip)
        self.groupBox_2.setToolTip(QCoreApplication.translate("Dialog", u"Criteria for the selection of ion images for export.", None))
#endif // QT_CONFIG(tooltip)
        self.groupBox_2.setTitle(QCoreApplication.translate("Dialog", u"Ion image selection", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Select ions with at least", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"pixels above intensity", None))
        self.button_cancel.setText(QCoreApplication.translate("Dialog", u"Cancel", None))
        self.button_save.setText(QCoreApplication.translate("Dialog", u"Save", None))
        self.groupBox.setTitle(QCoreApplication.translate("Dialog", u"Image filtering", None))
        self.check_box_gaussian_filter.setText(QCoreApplication.translate("Dialog", u"Enable Gaussian filtering", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Raw and Isotope corrected image winsorizing percentile", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Quantified image winsorizing percentile", None))
    # retranslateUi

