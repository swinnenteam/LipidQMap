# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiStandardCalculatorDialog.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDoubleSpinBox,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(961, 725)
        self.verticalLayout_3 = QVBoxLayout(Dialog)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.frame = QFrame(Dialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.groupBox = QGroupBox(self.frame)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.database_label = QLabel(self.groupBox)
        self.database_label.setObjectName(u"database_label")

        self.horizontalLayout_2.addWidget(self.database_label)

        self.database_combo_box = QComboBox(self.groupBox)
        self.database_combo_box.setObjectName(u"database_combo_box")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.database_combo_box.sizePolicy().hasHeightForWidth())
        self.database_combo_box.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.database_combo_box)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.verticalLayout_2.addWidget(self.label)

        self.standards_list_view = QListWidget(self.groupBox)
        self.standards_list_view.setObjectName(u"standards_list_view")

        self.verticalLayout_2.addWidget(self.standards_list_view)

        self.quantity_line_edit = QLineEdit(self.groupBox)
        self.quantity_line_edit.setObjectName(u"quantity_line_edit")

        self.verticalLayout_2.addWidget(self.quantity_line_edit)


        self.horizontalLayout_3.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(self.frame)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout = QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gridLayout_11 = QGridLayout()
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.label_mix_conc = QLabel(self.groupBox_2)
        self.label_mix_conc.setObjectName(u"label_mix_conc")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.label_mix_conc.setFont(font)

        self.gridLayout_11.addWidget(self.label_mix_conc, 0, 1, 1, 1)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_27 = QLabel(self.groupBox_2)
        self.label_27.setObjectName(u"label_27")

        self.gridLayout_3.addWidget(self.label_27, 1, 0, 1, 1)

        self.label_25 = QLabel(self.groupBox_2)
        self.label_25.setObjectName(u"label_25")

        self.gridLayout_3.addWidget(self.label_25, 0, 0, 1, 1)

        self.spinbox_final_mix_volume = QDoubleSpinBox(self.groupBox_2)
        self.spinbox_final_mix_volume.setObjectName(u"spinbox_final_mix_volume")
        self.spinbox_final_mix_volume.setDecimals(3)
        self.spinbox_final_mix_volume.setMaximum(1000.000000000000000)

        self.gridLayout_3.addWidget(self.spinbox_final_mix_volume, 3, 1, 1, 1)

        self.label_26 = QLabel(self.groupBox_2)
        self.label_26.setObjectName(u"label_26")

        self.gridLayout_3.addWidget(self.label_26, 0, 2, 1, 1)

        self.label_33 = QLabel(self.groupBox_2)
        self.label_33.setObjectName(u"label_33")

        self.gridLayout_3.addWidget(self.label_33, 4, 0, 1, 1)

        self.label_31 = QLabel(self.groupBox_2)
        self.label_31.setObjectName(u"label_31")

        self.gridLayout_3.addWidget(self.label_31, 3, 0, 1, 1)

        self.spinbox_molecular_weight = QDoubleSpinBox(self.groupBox_2)
        self.spinbox_molecular_weight.setObjectName(u"spinbox_molecular_weight")
        self.spinbox_molecular_weight.setDecimals(3)
        self.spinbox_molecular_weight.setMaximum(50000.000000000000000)

        self.gridLayout_3.addWidget(self.spinbox_molecular_weight, 4, 1, 1, 1)

        self.spinbox_stock_conc = QDoubleSpinBox(self.groupBox_2)
        self.spinbox_stock_conc.setObjectName(u"spinbox_stock_conc")
        self.spinbox_stock_conc.setMinimumSize(QSize(80, 0))
        self.spinbox_stock_conc.setDecimals(3)
        self.spinbox_stock_conc.setMaximum(10000.000000000000000)

        self.gridLayout_3.addWidget(self.spinbox_stock_conc, 0, 1, 1, 1)

        self.label_29 = QLabel(self.groupBox_2)
        self.label_29.setObjectName(u"label_29")

        self.gridLayout_3.addWidget(self.label_29, 2, 0, 1, 1)

        self.label_34 = QLabel(self.groupBox_2)
        self.label_34.setObjectName(u"label_34")

        self.gridLayout_3.addWidget(self.label_34, 4, 2, 1, 1)

        self.spinbox_working_dilution_factor = QDoubleSpinBox(self.groupBox_2)
        self.spinbox_working_dilution_factor.setObjectName(u"spinbox_working_dilution_factor")
        self.spinbox_working_dilution_factor.setMaximum(100000.000000000000000)

        self.gridLayout_3.addWidget(self.spinbox_working_dilution_factor, 1, 1, 1, 1)

        self.label_32 = QLabel(self.groupBox_2)
        self.label_32.setObjectName(u"label_32")

        self.gridLayout_3.addWidget(self.label_32, 3, 2, 1, 1)

        self.label_30 = QLabel(self.groupBox_2)
        self.label_30.setObjectName(u"label_30")

        self.gridLayout_3.addWidget(self.label_30, 2, 2, 1, 1)

        self.spinbox_volume_working_stock = QDoubleSpinBox(self.groupBox_2)
        self.spinbox_volume_working_stock.setObjectName(u"spinbox_volume_working_stock")
        self.spinbox_volume_working_stock.setDecimals(0)
        self.spinbox_volume_working_stock.setMaximum(10000.000000000000000)

        self.gridLayout_3.addWidget(self.spinbox_volume_working_stock, 2, 1, 1, 1)


        self.gridLayout_11.addLayout(self.gridLayout_3, 1, 1, 1, 1)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_5 = QLabel(self.groupBox_2)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 1, 0, 1, 1)

        self.label_12 = QLabel(self.groupBox_2)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout.addWidget(self.label_12, 4, 2, 1, 1)

        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 1, 2, 1, 1)

        self.spinbox_y_top = QSpinBox(self.groupBox_2)
        self.spinbox_y_top.setObjectName(u"spinbox_y_top")

        self.gridLayout.addWidget(self.spinbox_y_top, 3, 1, 1, 1)

        self.spinbox_margin = QSpinBox(self.groupBox_2)
        self.spinbox_margin.setObjectName(u"spinbox_margin")

        self.gridLayout.addWidget(self.spinbox_margin, 4, 1, 1, 1)

        self.label_7 = QLabel(self.groupBox_2)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout.addWidget(self.label_7, 2, 0, 1, 1)

        self.label_11 = QLabel(self.groupBox_2)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout.addWidget(self.label_11, 4, 0, 1, 1)

        self.label_8 = QLabel(self.groupBox_2)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout.addWidget(self.label_8, 2, 2, 1, 1)

        self.spinbox_x_left = QSpinBox(self.groupBox_2)
        self.spinbox_x_left.setObjectName(u"spinbox_x_left")
        self.spinbox_x_left.setMinimumSize(QSize(80, 0))

        self.gridLayout.addWidget(self.spinbox_x_left, 0, 1, 1, 1)

        self.spinbox_x_right = QSpinBox(self.groupBox_2)
        self.spinbox_x_right.setObjectName(u"spinbox_x_right")

        self.gridLayout.addWidget(self.spinbox_x_right, 1, 1, 1, 1)

        self.label_9 = QLabel(self.groupBox_2)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout.addWidget(self.label_9, 3, 0, 1, 1)

        self.label_3 = QLabel(self.groupBox_2)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)

        self.label_4 = QLabel(self.groupBox_2)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 0, 2, 1, 1)

        self.spinbox_y_bottom = QSpinBox(self.groupBox_2)
        self.spinbox_y_bottom.setObjectName(u"spinbox_y_bottom")

        self.gridLayout.addWidget(self.spinbox_y_bottom, 2, 1, 1, 1)

        self.label_10 = QLabel(self.groupBox_2)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout.addWidget(self.label_10, 3, 2, 1, 1)


        self.gridLayout_11.addLayout(self.gridLayout, 1, 0, 1, 1)

        self.label_surface_conc_result = QLabel(self.groupBox_2)
        self.label_surface_conc_result.setObjectName(u"label_surface_conc_result")
        self.label_surface_conc_result.setFont(font)

        self.gridLayout_11.addWidget(self.label_surface_conc_result, 4, 1, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_14 = QLabel(self.groupBox_2)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_2.addWidget(self.label_14, 0, 0, 1, 1)

        self.label_19 = QLabel(self.groupBox_2)
        self.label_19.setObjectName(u"label_19")

        self.gridLayout_2.addWidget(self.label_19, 2, 2, 1, 1)

        self.label_20 = QLabel(self.groupBox_2)
        self.label_20.setObjectName(u"label_20")

        self.gridLayout_2.addWidget(self.label_20, 3, 0, 1, 1)

        self.label_16 = QLabel(self.groupBox_2)
        self.label_16.setObjectName(u"label_16")

        self.gridLayout_2.addWidget(self.label_16, 1, 0, 1, 1)

        self.label_18 = QLabel(self.groupBox_2)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout_2.addWidget(self.label_18, 2, 0, 1, 1)

        self.label_17 = QLabel(self.groupBox_2)
        self.label_17.setObjectName(u"label_17")

        self.gridLayout_2.addWidget(self.label_17, 1, 2, 1, 1)

        self.spinbox_total_used_volume = QDoubleSpinBox(self.groupBox_2)
        self.spinbox_total_used_volume.setObjectName(u"spinbox_total_used_volume")
        self.spinbox_total_used_volume.setMinimumSize(QSize(80, 0))
        self.spinbox_total_used_volume.setDecimals(3)
        self.spinbox_total_used_volume.setMaximum(10000.000000000000000)

        self.gridLayout_2.addWidget(self.spinbox_total_used_volume, 0, 1, 1, 1)

        self.spinbox_syringe_flow = QDoubleSpinBox(self.groupBox_2)
        self.spinbox_syringe_flow.setObjectName(u"spinbox_syringe_flow")
        self.spinbox_syringe_flow.setDecimals(3)
        self.spinbox_syringe_flow.setMaximum(10000.000000000000000)

        self.gridLayout_2.addWidget(self.spinbox_syringe_flow, 1, 1, 1, 1)

        self.spinbox_drying_time = QDoubleSpinBox(self.groupBox_2)
        self.spinbox_drying_time.setObjectName(u"spinbox_drying_time")
        self.spinbox_drying_time.setDecimals(3)
        self.spinbox_drying_time.setMaximum(1000.000000000000000)

        self.gridLayout_2.addWidget(self.spinbox_drying_time, 2, 1, 1, 1)

        self.label_15 = QLabel(self.groupBox_2)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_2.addWidget(self.label_15, 0, 2, 1, 1)

        self.label_21 = QLabel(self.groupBox_2)
        self.label_21.setObjectName(u"label_21")

        self.gridLayout_2.addWidget(self.label_21, 3, 2, 1, 1)

        self.label_22 = QLabel(self.groupBox_2)
        self.label_22.setObjectName(u"label_22")

        self.gridLayout_2.addWidget(self.label_22, 4, 0, 1, 1)

        self.spinbox_initial_equilibration = QDoubleSpinBox(self.groupBox_2)
        self.spinbox_initial_equilibration.setObjectName(u"spinbox_initial_equilibration")
        self.spinbox_initial_equilibration.setDecimals(3)
        self.spinbox_initial_equilibration.setMaximum(1000.000000000000000)

        self.gridLayout_2.addWidget(self.spinbox_initial_equilibration, 4, 1, 1, 1)

        self.label_23 = QLabel(self.groupBox_2)
        self.label_23.setObjectName(u"label_23")

        self.gridLayout_2.addWidget(self.label_23, 4, 2, 1, 1)

        self.spinbox_drying_cycles = QSpinBox(self.groupBox_2)
        self.spinbox_drying_cycles.setObjectName(u"spinbox_drying_cycles")

        self.gridLayout_2.addWidget(self.spinbox_drying_cycles, 3, 1, 1, 1)


        self.gridLayout_11.addLayout(self.gridLayout_2, 4, 0, 1, 1)

        self.label_volume = QLabel(self.groupBox_2)
        self.label_volume.setObjectName(u"label_volume")
        self.label_volume.setFont(font)

        self.gridLayout_11.addWidget(self.label_volume, 3, 0, 1, 1)

        self.label_area = QLabel(self.groupBox_2)
        self.label_area.setObjectName(u"label_area")
        self.label_area.setFont(font)

        self.gridLayout_11.addWidget(self.label_area, 0, 0, 1, 1)

        self.label_surface_conc = QLabel(self.groupBox_2)
        self.label_surface_conc.setObjectName(u"label_surface_conc")
        self.label_surface_conc.setFont(font)

        self.gridLayout_11.addWidget(self.label_surface_conc, 3, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_11.addItem(self.verticalSpacer, 2, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_11.addItem(self.verticalSpacer_2, 2, 1, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_11)

        self.apply_button = QPushButton(self.groupBox_2)
        self.apply_button.setObjectName(u"apply_button")
        self.apply_button.setMinimumSize(QSize(200, 0))
        self.apply_button.setMaximumSize(QSize(250, 16777215))

        self.verticalLayout.addWidget(self.apply_button)


        self.horizontalLayout_3.addWidget(self.groupBox_2)


        self.verticalLayout_3.addWidget(self.frame)

        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_2, 0, 0, 1, 1)

        self.save_button = QPushButton(Dialog)
        self.save_button.setObjectName(u"save_button")

        self.gridLayout_4.addWidget(self.save_button, 0, 2, 1, 1)

        self.cancel_button = QPushButton(Dialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout_4.addWidget(self.cancel_button, 0, 1, 1, 1)


        self.verticalLayout_3.addLayout(self.gridLayout_4)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Standard calculator", None))
        self.groupBox.setTitle(QCoreApplication.translate("Dialog", u"Database standard concentrations", None))
        self.database_label.setText(QCoreApplication.translate("Dialog", u"Database:", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Standards:", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("Dialog", u"Standard concentration calculator", None))
        self.label_mix_conc.setText(QCoreApplication.translate("Dialog", u"3. Spraying mix concentration: () pmol/mL", None))
        self.label_27.setText(QCoreApplication.translate("Dialog", u"Working stock dilution factor", None))
        self.label_25.setText(QCoreApplication.translate("Dialog", u"Stock concentration", None))
        self.label_26.setText(QCoreApplication.translate("Dialog", u"mg/mL", None))
        self.label_33.setText(QCoreApplication.translate("Dialog", u"Molecular weight", None))
        self.label_31.setText(QCoreApplication.translate("Dialog", u"Volume of final IS mixture", None))
        self.label_29.setText(QCoreApplication.translate("Dialog", u"Volume working stock used", None))
        self.label_34.setText(QCoreApplication.translate("Dialog", u"g/mol", None))
        self.label_32.setText(QCoreApplication.translate("Dialog", u"mL", None))
        self.label_30.setText(QCoreApplication.translate("Dialog", u"\u03bcL", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"X right dimension", None))
        self.label_12.setText(QCoreApplication.translate("Dialog", u"mm", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"mm", None))
        self.label_7.setText(QCoreApplication.translate("Dialog", u"Y bottom dimension", None))
        self.label_11.setText(QCoreApplication.translate("Dialog", u"Margin", None))
        self.label_8.setText(QCoreApplication.translate("Dialog", u"mm", None))
        self.label_9.setText(QCoreApplication.translate("Dialog", u"Y top dimension", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"X left dimension", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"mm", None))
        self.label_10.setText(QCoreApplication.translate("Dialog", u"mm", None))
        self.label_surface_conc_result.setText(QCoreApplication.translate("Dialog", u"() pmol/mm2", None))
        self.label_14.setText(QCoreApplication.translate("Dialog", u"Total used volume", None))
        self.label_19.setText(QCoreApplication.translate("Dialog", u"minutes", None))
        self.label_20.setText(QCoreApplication.translate("Dialog", u"Drying cycles", None))
        self.label_16.setText(QCoreApplication.translate("Dialog", u"Syringe pump flow", None))
        self.label_18.setText(QCoreApplication.translate("Dialog", u"Drying time", None))
        self.label_17.setText(QCoreApplication.translate("Dialog", u"mL/minute", None))
        self.label_15.setText(QCoreApplication.translate("Dialog", u"mL", None))
        self.label_21.setText(QCoreApplication.translate("Dialog", u"cycles", None))
        self.label_22.setText(QCoreApplication.translate("Dialog", u"Initial equilibration time", None))
        self.label_23.setText(QCoreApplication.translate("Dialog", u"minutes", None))
        self.label_volume.setText(QCoreApplication.translate("Dialog", u"2. Volume sprayed: () mL", None))
        self.label_area.setText(QCoreApplication.translate("Dialog", u"1. Area: () mm2", None))
        self.label_surface_conc.setText(QCoreApplication.translate("Dialog", u"4. Sprayed on surface", None))
        self.apply_button.setText(QCoreApplication.translate("Dialog", u"<- Apply", None))
        self.save_button.setText(QCoreApplication.translate("Dialog", u"Save && Close", None))
        self.cancel_button.setText(QCoreApplication.translate("Dialog", u"Cancel", None))
    # retranslateUi

