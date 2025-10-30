# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiImportDialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QDoubleSpinBox, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QProgressBar, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QTableView,
    QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(455, 806)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.open_imzml_button = QPushButton(Dialog)
        self.open_imzml_button.setObjectName(u"open_imzml_button")

        self.horizontalLayout.addWidget(self.open_imzml_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.imzml_list_view = QTableView(Dialog)
        self.imzml_list_view.setObjectName(u"imzml_list_view")

        self.verticalLayout.addWidget(self.imzml_list_view)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, 0, -1, -1)
        self.ppm_spinbox = QDoubleSpinBox(Dialog)
        self.ppm_spinbox.setObjectName(u"ppm_spinbox")
        self.ppm_spinbox.setMinimumSize(QSize(100, 0))
        self.ppm_spinbox.setBaseSize(QSize(0, 0))
        self.ppm_spinbox.setMinimum(0.050000000000000)
        self.ppm_spinbox.setValue(10.000000000000000)

        self.gridLayout.addWidget(self.ppm_spinbox, 0, 1, 1, 1)

        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 2, 0, 1, 1)

        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)

        self.imputation_checkbox = QCheckBox(Dialog)
        self.imputation_checkbox.setObjectName(u"imputation_checkbox")

        self.gridLayout.addWidget(self.imputation_checkbox, 1, 1, 1, 2)

        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 1, 0, 1, 1)

        self.database_combo_box = QComboBox(Dialog)
        self.database_combo_box.setObjectName(u"database_combo_box")

        self.gridLayout.addWidget(self.database_combo_box, 2, 1, 1, 3)

        self.bin_size_spinbox = QDoubleSpinBox(Dialog)
        self.bin_size_spinbox.setObjectName(u"bin_size_spinbox")
        self.bin_size_spinbox.setMinimum(0.010000000000000)
        self.bin_size_spinbox.setMaximum(100.000000000000000)
        self.bin_size_spinbox.setSingleStep(0.100000000000000)
        self.bin_size_spinbox.setValue(5.000000000000000)

        self.gridLayout.addWidget(self.bin_size_spinbox, 0, 3, 1, 1)

        self.label_9 = QLabel(Dialog)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout.addWidget(self.label_9, 0, 2, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_3, 1, 3, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.isotope_group_box = QGroupBox(Dialog)
        self.isotope_group_box.setObjectName(u"isotope_group_box")
        self.verticalLayout_3 = QVBoxLayout(self.isotope_group_box)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.na_iso_cor_checkbox = QCheckBox(self.isotope_group_box)
        self.na_iso_cor_checkbox.setObjectName(u"na_iso_cor_checkbox")

        self.verticalLayout_3.addWidget(self.na_iso_cor_checkbox)

        self.m2_iso_cor_checkbox = QCheckBox(self.isotope_group_box)
        self.m2_iso_cor_checkbox.setObjectName(u"m2_iso_cor_checkbox")

        self.verticalLayout_3.addWidget(self.m2_iso_cor_checkbox)


        self.verticalLayout.addWidget(self.isotope_group_box)

        self.cal_group_box = QGroupBox(Dialog)
        self.cal_group_box.setObjectName(u"cal_group_box")
        self.cal_group_box.setMinimumSize(QSize(0, 0))
        self.verticalLayout_2 = QVBoxLayout(self.cal_group_box)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_7 = QLabel(self.cal_group_box)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_2.addWidget(self.label_7, 4, 0, 1, 1)

        self.label_2 = QLabel(self.cal_group_box)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_2.addWidget(self.label_2, 2, 0, 1, 1)

        self.label_8 = QLabel(self.cal_group_box)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout_2.addWidget(self.label_8, 1, 0, 1, 1)

        self.cal_checkbox = QCheckBox(self.cal_group_box)
        self.cal_checkbox.setObjectName(u"cal_checkbox")

        self.gridLayout_2.addWidget(self.cal_checkbox, 0, 0, 1, 1)

        self.cal_ppm_spinbox = QDoubleSpinBox(self.cal_group_box)
        self.cal_ppm_spinbox.setObjectName(u"cal_ppm_spinbox")

        self.gridLayout_2.addWidget(self.cal_ppm_spinbox, 3, 1, 1, 1)

        self.label_6 = QLabel(self.cal_group_box)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_2.addWidget(self.label_6, 3, 0, 1, 1)

        self.cal_int_spinbox = QSpinBox(self.cal_group_box)
        self.cal_int_spinbox.setObjectName(u"cal_int_spinbox")
        self.cal_int_spinbox.setMinimum(100)
        self.cal_int_spinbox.setMaximum(1000000)
        self.cal_int_spinbox.setSingleStep(100)
        self.cal_int_spinbox.setValue(10000)

        self.gridLayout_2.addWidget(self.cal_int_spinbox, 4, 1, 1, 1)

        self.calibrant_pos_spinbox = QDoubleSpinBox(self.cal_group_box)
        self.calibrant_pos_spinbox.setObjectName(u"calibrant_pos_spinbox")
        self.calibrant_pos_spinbox.setDecimals(5)
        self.calibrant_pos_spinbox.setMaximum(10000.000000000000000)

        self.gridLayout_2.addWidget(self.calibrant_pos_spinbox, 1, 1, 1, 1)

        self.calibrant_neg_spinbox = QDoubleSpinBox(self.cal_group_box)
        self.calibrant_neg_spinbox.setObjectName(u"calibrant_neg_spinbox")
        self.calibrant_neg_spinbox.setDecimals(5)
        self.calibrant_neg_spinbox.setMaximum(10000.000000000000000)

        self.gridLayout_2.addWidget(self.calibrant_neg_spinbox, 2, 1, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_2, 0, 1, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_2)


        self.verticalLayout.addWidget(self.cal_group_box)

        self.progress_bar_overall = QProgressBar(Dialog)
        self.progress_bar_overall.setObjectName(u"progress_bar_overall")
        self.progress_bar_overall.setValue(0)

        self.verticalLayout.addWidget(self.progress_bar_overall)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.progress_bar_file = QProgressBar(Dialog)
        self.progress_bar_file.setObjectName(u"progress_bar_file")
        self.progress_bar_file.setValue(0)

        self.horizontalLayout_2.addWidget(self.progress_bar_file)

        self.import_data_button = QPushButton(Dialog)
        self.import_data_button.setObjectName(u"import_data_button")

        self.horizontalLayout_2.addWidget(self.import_data_button)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Import imzML files", None))
#if QT_CONFIG(tooltip)
        self.label.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-family:'-apple-system','system-ui','sans-serif'; font-size:13px; color:#cccccc; background-color:#181818;\">LipidQMap determines the ion mode of each imzML automatically. When it finds one positive-mode file and one negative-mode file with matching names (differing only by \u201cpos\u201d or \u201cneg\u201d), it merges them into a single image stack.</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("Dialog", u"Select imzML files \u24d8:", None))
        self.open_imzml_button.setText(QCoreApplication.translate("Dialog", u"Open Files", None))
        self.ppm_spinbox.setSuffix(QCoreApplication.translate("Dialog", u" ppm", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"Database:", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Accuracy:", None))
#if QT_CONFIG(tooltip)
        self.imputation_checkbox.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-size:14pt;\">Enables median imputation to fill in pixels with no signal, using the values of 3x3 surrounding pixels.</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.imputation_checkbox.setText(QCoreApplication.translate("Dialog", u"Fill in missing pixel values \u24d8", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Imputation:", None))
#if QT_CONFIG(tooltip)
        self.bin_size_spinbox.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-size:14pt;\">Width of the bin of the average mz spectrum at mz 1000, in miliDalton. For calculating the average mz spectrum of an image section, a binning algorithm is used. This spectrum averaging algoritm assigns peaks accross the spectra of different pixels to mz bins and then calculates the average intensity for each bin.</span></p><p><span style=\" font-size:14pt;\">The width of the bins is automatically adjusted depending on the mz, by keeping a constant ppm. For example if a bin size of 5 mDa is provided (at mz 1000) this corresponds to a ppm of 5. At for example mz 700, a ppm of 5 corresponds to a bin size of 3.5 mDa, at mz 400 the bin size will be 2 mDa , etc...</span></p><p><span style=\" font-size:14pt;\">This setting only affects the average spectrum that is shown in the spectrum viewer, it has no consequence on the extracted ion images.</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.bin_size_spinbox.setSuffix(QCoreApplication.translate("Dialog", u" mDa", u"miliDalton"))
        self.label_9.setText(QCoreApplication.translate("Dialog", u"Bin size:", None))
        self.isotope_group_box.setTitle(QCoreApplication.translate("Dialog", u"Isotopic correction", None))
#if QT_CONFIG(tooltip)
        self.na_iso_cor_checkbox.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-size:14pt;\">Type II isotopic correction for isobaric overlap between [M+H]+ and [M+Na]+ adduct forms. For protonated lipid ions, the sodiated adduct of species [X:Y] (X number of C atoms and Y number of double bonds in the acyl chains) overlaps with species [X+2:Y+3]. The correction algorith is described in H\u00f6ring at el., </span><span style=\" font-size:14pt; font-style:italic;\">Anal. Chem. 2020, 92, 16, 10966\u201310970. </span></p><p><span style=\" font-size:14pt;\">This correction is relevant for measurements with a mass resolution lower than +/- 600.000 (m/z difference 0.0025).</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.na_iso_cor_checkbox.setText(QCoreApplication.translate("Dialog", u"Correct [M+H]+ for [M+Na]+ overlap \u24d8", None))
#if QT_CONFIG(tooltip)
        self.m2_iso_cor_checkbox.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-size:14pt;\">Type II isotopic correction for isobaric overlap between the (M+2) isotopologue of a species and the corresponding species from the same class with 1 double bond less. </span></p><p><span style=\" font-size:14pt;\">This correction is relevant for measurements with a mass resolution lower than +/- 180.000 (m/z difference 0.0089).</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.m2_iso_cor_checkbox.setText(QCoreApplication.translate("Dialog", u"Correct for M+2 double bond isotopologues overlap \u24d8", None))
        self.cal_group_box.setTitle(QCoreApplication.translate("Dialog", u"Online calibration settings", None))
        self.label_7.setText(QCoreApplication.translate("Dialog", u"Minimum intensity:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Calibrate on m/z (negative ion):", None))
        self.label_8.setText(QCoreApplication.translate("Dialog", u"Calibrate on m/z (positive ion):", None))
        self.cal_checkbox.setText(QCoreApplication.translate("Dialog", u"Apply online calibration", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"Peak assignment tolerance (ppm):", None))
        self.import_data_button.setText(QCoreApplication.translate("Dialog", u"Import data", None))
    # retranslateUi

