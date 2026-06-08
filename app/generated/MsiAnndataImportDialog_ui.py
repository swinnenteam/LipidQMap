# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiAnndataImportDialog.ui'
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
    QDoubleSpinBox, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QProgressBar, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(455, 520)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.open_anndata_button = QPushButton(Dialog)
        self.open_anndata_button.setObjectName(u"open_anndata_button")

        self.horizontalLayout.addWidget(self.open_anndata_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.anndata_path_line_edit = QLineEdit(Dialog)
        self.anndata_path_line_edit.setObjectName(u"anndata_path_line_edit")
        self.anndata_path_line_edit.setReadOnly(True)

        self.verticalLayout.addWidget(self.anndata_path_line_edit)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)

        self.ppm_spinbox = QDoubleSpinBox(Dialog)
        self.ppm_spinbox.setObjectName(u"ppm_spinbox")
        self.ppm_spinbox.setMinimumSize(QSize(100, 0))
        self.ppm_spinbox.setMinimum(0.050000000000000)
        self.ppm_spinbox.setValue(10.000000000000000)

        self.gridLayout.addWidget(self.ppm_spinbox, 0, 1, 1, 1)

        self.label_matrix = QLabel(Dialog)
        self.label_matrix.setObjectName(u"label_matrix")

        self.gridLayout.addWidget(self.label_matrix, 1, 0, 1, 1)

        self.matrix_combo_box = QComboBox(Dialog)
        self.matrix_combo_box.setObjectName(u"matrix_combo_box")

        self.gridLayout.addWidget(self.matrix_combo_box, 1, 1, 1, 3)

        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 1)

        self.imputation_checkbox = QCheckBox(Dialog)
        self.imputation_checkbox.setObjectName(u"imputation_checkbox")

        self.gridLayout.addWidget(self.imputation_checkbox, 2, 1, 1, 3)

        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 3, 0, 1, 1)

        self.database_combo_box = QComboBox(Dialog)
        self.database_combo_box.setObjectName(u"database_combo_box")

        self.gridLayout.addWidget(self.database_combo_box, 3, 1, 1, 3)


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

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Import AnnData/MuData file", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Select AnnData/MuData file:", None))
        self.open_anndata_button.setText(QCoreApplication.translate("Dialog", u"Open File", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Accuracy:", None))
        self.ppm_spinbox.setSuffix(QCoreApplication.translate("Dialog", u" ppm", None))
        self.label_matrix.setText(QCoreApplication.translate("Dialog", u"Data matrix:", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Imputation:", None))
#if QT_CONFIG(tooltip)
        self.imputation_checkbox.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Enables median imputation to fill in pixels with no signal, using the values of 3x3 surrounding pixels. AnnData background pixels remain transparent.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.imputation_checkbox.setText(QCoreApplication.translate("Dialog", u"Fill in missing pixel values \u24d8", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"Database:", None))
        self.isotope_group_box.setTitle(QCoreApplication.translate("Dialog", u"Isotopic correction", None))
        self.na_iso_cor_checkbox.setText(QCoreApplication.translate("Dialog", u"Correct [M+H]+ for [M+Na]+ overlap \u24d8", None))
        self.m2_iso_cor_checkbox.setText(QCoreApplication.translate("Dialog", u"Correct for M+2 double bond isotopologues overlap \u24d8", None))
        self.import_data_button.setText(QCoreApplication.translate("Dialog", u"Import data", None))
    # retranslateUi

