# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiSettingsDialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QDoubleSpinBox,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QSpinBox, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(621, 430)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
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


        self.gridLayout.addLayout(self.horizontalLayout, 5, 0, 1, 1)

        self.groupBox = QGroupBox(Dialog)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.check_box_gaussian_filter = QCheckBox(self.groupBox)
        self.check_box_gaussian_filter.setObjectName(u"check_box_gaussian_filter")

        self.gridLayout_2.addWidget(self.check_box_gaussian_filter, 0, 0, 1, 1)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFormAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.label)

        self.spinbox_winsor_quant = QDoubleSpinBox(self.groupBox)
        self.spinbox_winsor_quant.setObjectName(u"spinbox_winsor_quant")
        self.spinbox_winsor_quant.setMinimumSize(QSize(65, 0))
        self.spinbox_winsor_quant.setDecimals(1)
        self.spinbox_winsor_quant.setValue(99.000000000000000)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.spinbox_winsor_quant)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.label_2)

        self.spinbox_winsor_raw = QDoubleSpinBox(self.groupBox)
        self.spinbox_winsor_raw.setObjectName(u"spinbox_winsor_raw")
        self.spinbox_winsor_raw.setMinimumSize(QSize(65, 0))
        self.spinbox_winsor_raw.setDecimals(1)
        self.spinbox_winsor_raw.setValue(99.000000000000000)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.spinbox_winsor_raw)


        self.gridLayout_2.addLayout(self.formLayout, 1, 0, 1, 2)


        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 4, 0, 1, 1)

        self.groupBox_2 = QGroupBox(Dialog)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout_4 = QGridLayout(self.groupBox_2)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.radio_selection_threshold = QRadioButton(self.groupBox_2)
        self.radio_selection_threshold.setObjectName(u"radio_selection_threshold")
        self.radio_selection_threshold.setChecked(True)

        self.gridLayout_4.addWidget(self.radio_selection_threshold, 0, 0, 1, 1)

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


        self.gridLayout_4.addLayout(self.gridLayout_3, 1, 0, 1, 1)

        self.radio_selection_feature = QRadioButton(self.groupBox_2)
        self.radio_selection_feature.setObjectName(u"radio_selection_feature")

        self.gridLayout_4.addWidget(self.radio_selection_feature, 2, 0, 1, 1)

        self.gridLayout_feature_selection = QGridLayout()
        self.gridLayout_feature_selection.setObjectName(u"gridLayout_feature_selection")
        self.label_feature_noise = QLabel(self.groupBox_2)
        self.label_feature_noise.setObjectName(u"label_feature_noise")

        self.gridLayout_feature_selection.addWidget(self.label_feature_noise, 0, 0, 1, 1)

        self.spinbox_feature_noise_sigma = QDoubleSpinBox(self.groupBox_2)
        self.spinbox_feature_noise_sigma.setObjectName(u"spinbox_feature_noise_sigma")
        self.spinbox_feature_noise_sigma.setDecimals(1)
        self.spinbox_feature_noise_sigma.setMinimum(0.000000000000000)
        self.spinbox_feature_noise_sigma.setMaximum(100.000000000000000)
        self.spinbox_feature_noise_sigma.setSingleStep(0.500000000000000)
        self.spinbox_feature_noise_sigma.setValue(5.000000000000000)

        self.gridLayout_feature_selection.addWidget(self.spinbox_feature_noise_sigma, 0, 1, 1, 1)

        self.label_feature_sigma = QLabel(self.groupBox_2)
        self.label_feature_sigma.setObjectName(u"label_feature_sigma")

        self.gridLayout_feature_selection.addWidget(self.label_feature_sigma, 0, 2, 1, 1)

        self.label_feature_pixels = QLabel(self.groupBox_2)
        self.label_feature_pixels.setObjectName(u"label_feature_pixels")

        self.gridLayout_feature_selection.addWidget(self.label_feature_pixels, 1, 0, 1, 1)

        self.spinbox_feature_min_pixels = QSpinBox(self.groupBox_2)
        self.spinbox_feature_min_pixels.setObjectName(u"spinbox_feature_min_pixels")
        self.spinbox_feature_min_pixels.setMinimum(1)
        self.spinbox_feature_min_pixels.setMaximum(10000000)
        self.spinbox_feature_min_pixels.setSingleStep(5)
        self.spinbox_feature_min_pixels.setValue(25)

        self.gridLayout_feature_selection.addWidget(self.spinbox_feature_min_pixels, 1, 1, 1, 1)


        self.gridLayout_4.addLayout(self.gridLayout_feature_selection, 3, 0, 1, 1)


        self.gridLayout.addWidget(self.groupBox_2, 1, 0, 1, 1)

        self.groupBox_scalebar = QGroupBox(Dialog)
        self.groupBox_scalebar.setObjectName(u"groupBox_scalebar")
        self.gridLayout_scalebar = QGridLayout(self.groupBox_scalebar)
        self.gridLayout_scalebar.setObjectName(u"gridLayout_scalebar")
        self.check_box_scalebar_enabled = QCheckBox(self.groupBox_scalebar)
        self.check_box_scalebar_enabled.setObjectName(u"check_box_scalebar_enabled")
        self.check_box_scalebar_enabled.setChecked(True)

        self.gridLayout_scalebar.addWidget(self.check_box_scalebar_enabled, 0, 0, 1, 2)

        self.radio_scalebar_auto = QRadioButton(self.groupBox_scalebar)
        self.radio_scalebar_auto.setObjectName(u"radio_scalebar_auto")

        self.gridLayout_scalebar.addWidget(self.radio_scalebar_auto, 1, 0, 1, 1)

        self.label_scalebar_auto_value = QLabel(self.groupBox_scalebar)
        self.label_scalebar_auto_value.setObjectName(u"label_scalebar_auto_value")

        self.gridLayout_scalebar.addWidget(self.label_scalebar_auto_value, 1, 1, 1, 1)

        self.radio_scalebar_manual = QRadioButton(self.groupBox_scalebar)
        self.radio_scalebar_manual.setObjectName(u"radio_scalebar_manual")

        self.gridLayout_scalebar.addWidget(self.radio_scalebar_manual, 2, 0, 1, 1)

        self.spinbox_scalebar_manual = QSpinBox(self.groupBox_scalebar)
        self.spinbox_scalebar_manual.setObjectName(u"spinbox_scalebar_manual")
        self.spinbox_scalebar_manual.setEnabled(False)
        self.spinbox_scalebar_manual.setMinimum(10)
        self.spinbox_scalebar_manual.setMaximum(100000)
        self.spinbox_scalebar_manual.setSingleStep(10)
        self.spinbox_scalebar_manual.setValue(100)

        self.gridLayout_scalebar.addWidget(self.spinbox_scalebar_manual, 2, 1, 1, 1)


        self.gridLayout.addWidget(self.groupBox_scalebar, 3, 0, 1, 1)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Settings", None))
        self.button_cancel.setText(QCoreApplication.translate("Dialog", u"Close", None))
        self.button_save.setText(QCoreApplication.translate("Dialog", u"Apply", None))
        self.groupBox.setTitle(QCoreApplication.translate("Dialog", u"Image filtering", None))
        self.check_box_gaussian_filter.setText(QCoreApplication.translate("Dialog", u"Enable Gaussian filtering", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Raw and Isotope corrected image winsorizing percentile", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Quantified image winsorizing percentile", None))
#if QT_CONFIG(tooltip)
        self.groupBox_2.setToolTip(QCoreApplication.translate("Dialog", u"Criteria for the selection of ion images for export.", None))
#endif // QT_CONFIG(tooltip)
        self.groupBox_2.setTitle(QCoreApplication.translate("Dialog", u"Ion image selection", None))
        self.radio_selection_threshold.setText(QCoreApplication.translate("Dialog", u"Intensity threshold", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Select ions with at least", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"pixels above intensity", None))
        self.radio_selection_feature.setText(QCoreApplication.translate("Dialog", u"Feature-like region", None))
        self.label_feature_noise.setText(QCoreApplication.translate("Dialog", u"Noise threshold", None))
        self.label_feature_sigma.setText(QCoreApplication.translate("Dialog", u"robust \u03c3 above background", None))
        self.label_feature_pixels.setText(QCoreApplication.translate("Dialog", u"Minimum connected feature pixels", None))
        self.groupBox_scalebar.setTitle(QCoreApplication.translate("Dialog", u"Scale bar", None))
        self.check_box_scalebar_enabled.setText(QCoreApplication.translate("Dialog", u"Show scale bars", None))
        self.radio_scalebar_auto.setText(QCoreApplication.translate("Dialog", u"Auto length", None))
        self.label_scalebar_auto_value.setText("")
        self.radio_scalebar_manual.setText(QCoreApplication.translate("Dialog", u"Manual length", None))
        self.spinbox_scalebar_manual.setSuffix(QCoreApplication.translate("Dialog", u" um", None))
    # retranslateUi

