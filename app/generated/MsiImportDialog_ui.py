# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiImportDialog.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QComboBox,
    QDialog, QDoubleSpinBox, QGridLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QProgressBar,
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(350, 400)
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

        self.imzml_list_view = QListWidget(Dialog)
        self.imzml_list_view.setObjectName(u"imzml_list_view")
        self.imzml_list_view.setFocusPolicy(Qt.NoFocus)
        self.imzml_list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.imzml_list_view.setProperty("showDropIndicator", False)
        self.imzml_list_view.setSelectionMode(QAbstractItemView.NoSelection)

        self.verticalLayout.addWidget(self.imzml_list_view)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, 0, -1, -1)
        self.neg_radio_button = QRadioButton(Dialog)
        self.button_group = QButtonGroup(Dialog)
        self.button_group.setObjectName(u"button_group")
        self.button_group.addButton(self.neg_radio_button)
        self.neg_radio_button.setObjectName(u"neg_radio_button")

        self.gridLayout.addWidget(self.neg_radio_button, 0, 2, 1, 1)

        self.pos_radio_button = QRadioButton(Dialog)
        self.button_group.addButton(self.pos_radio_button)
        self.pos_radio_button.setObjectName(u"pos_radio_button")
        self.pos_radio_button.setChecked(True)

        self.gridLayout.addWidget(self.pos_radio_button, 0, 1, 1, 1)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 0, 3, 1, 1)

        self.ppm_spin_box = QDoubleSpinBox(Dialog)
        self.ppm_spin_box.setObjectName(u"ppm_spin_box")
        self.ppm_spin_box.setMinimum(0.050000000000000)
        self.ppm_spin_box.setValue(10.000000000000000)

        self.gridLayout.addWidget(self.ppm_spin_box, 1, 1, 1, 1)

        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)

        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 1, 2, 1, 1)

        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 2, 0, 1, 1)

        self.database_combo_box = QComboBox(Dialog)
        self.database_combo_box.setObjectName(u"database_combo_box")

        self.gridLayout.addWidget(self.database_combo_box, 2, 1, 1, 3)


        self.verticalLayout.addLayout(self.gridLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.progress_bar = QProgressBar(Dialog)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(0)

        self.horizontalLayout_2.addWidget(self.progress_bar)

        self.import_data_button = QPushButton(Dialog)
        self.import_data_button.setObjectName(u"import_data_button")

        self.horizontalLayout_2.addWidget(self.import_data_button)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Import imzML files", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Select imzML files:", None))
        self.open_imzml_button.setText(QCoreApplication.translate("Dialog", u"Open Files", None))
        self.neg_radio_button.setText(QCoreApplication.translate("Dialog", u"Negative", None))
        self.pos_radio_button.setText(QCoreApplication.translate("Dialog", u"Positive", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Ion mode:", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Accuracy:", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"ppm", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"Database:", None))
        self.import_data_button.setText(QCoreApplication.translate("Dialog", u"Import data", None))
    # retranslateUi

