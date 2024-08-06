# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiAboutDialog.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(567, 302)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(26)
        font.setBold(False)
        self.label.setFont(font)

        self.verticalLayout_2.addWidget(self.label)

        self.label_version = QLabel(Dialog)
        self.label_version.setObjectName(u"label_version")

        self.verticalLayout_2.addWidget(self.label_version)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.line = QFrame(Dialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line)


        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")
        font1 = QFont()
        font1.setPointSize(16)
        self.label_3.setFont(font1)

        self.verticalLayout.addWidget(self.label_3)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_15 = QLabel(Dialog)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_3.addWidget(self.label_15, 3, 4, 1, 1)

        self.label_7 = QLabel(Dialog)
        self.label_7.setObjectName(u"label_7")
        font2 = QFont()
        font2.setBold(True)
        self.label_7.setFont(font2)
        self.label_7.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_7, 4, 0, 1, 1)

        self.label_8 = QLabel(Dialog)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setFont(font2)
        self.label_8.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_8, 1, 3, 1, 1)

        self.label_14 = QLabel(Dialog)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_3.addWidget(self.label_14, 1, 4, 1, 1)

        self.label_12 = QLabel(Dialog)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout_3.addWidget(self.label_12, 3, 1, 1, 1)

        self.label_6 = QLabel(Dialog)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font2)
        self.label_6.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_6, 3, 0, 1, 1)

        self.label_10 = QLabel(Dialog)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout_3.addWidget(self.label_10, 1, 1, 1, 1)

        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font2)
        self.label_4.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_4, 1, 0, 1, 1)

        self.label_11 = QLabel(Dialog)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout_3.addWidget(self.label_11, 2, 1, 1, 1)

        self.label_9 = QLabel(Dialog)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font2)
        self.label_9.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_9, 3, 3, 1, 1)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font2)

        self.gridLayout_3.addWidget(self.label_2, 2, 3, 1, 1)

        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font2)
        self.label_5.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_5, 2, 0, 1, 1)

        self.label_13 = QLabel(Dialog)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout_3.addWidget(self.label_13, 4, 1, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_2, 2, 2, 1, 1)

        self.label_16 = QLabel(Dialog)
        self.label_16.setObjectName(u"label_16")

        self.gridLayout_3.addWidget(self.label_16, 2, 4, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_3)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.button_close = QPushButton(Dialog)
        self.button_close.setObjectName(u"button_close")

        self.horizontalLayout.addWidget(self.button_close)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"About", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"LipidQuantMSI", None))
        self.label_version.setText(QCoreApplication.translate("Dialog", u"Version: 1.0.0", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Keyboard shortcuts:", None))
        self.label_15.setText(QCoreApplication.translate("Dialog", u"Select/unselect species for export", None))
        self.label_7.setText(QCoreApplication.translate("Dialog", u"G", None))
        self.label_8.setText(QCoreApplication.translate("Dialog", u"Up / Down", None))
        self.label_14.setText(QCoreApplication.translate("Dialog", u"Select species", None))
        self.label_12.setText(QCoreApplication.translate("Dialog", u"Toggle Quantitative view", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"Q", None))
        self.label_10.setText(QCoreApplication.translate("Dialog", u"Toggle Raw data view", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"R", None))
        self.label_11.setText(QCoreApplication.translate("Dialog", u"Toggle Isotope Corrected view", None))
        self.label_9.setText(QCoreApplication.translate("Dialog", u"Space", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Left/Right", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"I", None))
        self.label_13.setText(QCoreApplication.translate("Dialog", u"Toggle global scale across all images", None))
        self.label_16.setText(QCoreApplication.translate("Dialog", u"Go to next checked species", None))
        self.button_close.setText(QCoreApplication.translate("Dialog", u"Close", None))
    # retranslateUi

