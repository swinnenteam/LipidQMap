# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiMainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QMainWindow, QMenu,
    QMenuBar, QScrollArea, QSizePolicy, QSplitter,
    QStatusBar, QTabWidget, QTableView, QToolBar,
    QVBoxLayout, QWidget)
from . import resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.action_open_imzml_dialog = QAction(MainWindow)
        self.action_open_imzml_dialog.setObjectName(u"action_open_imzml_dialog")
        icon = QIcon()
        icon.addFile(u":/images/icons/open_file.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_open_imzml_dialog.setIcon(icon)
        self.action_save_images = QAction(MainWindow)
        self.action_save_images.setObjectName(u"action_save_images")
        icon1 = QIcon()
        icon1.addFile(u":/images/icons/save.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_save_images.setIcon(icon1)
        self.action_zoom_in = QAction(MainWindow)
        self.action_zoom_in.setObjectName(u"action_zoom_in")
        icon2 = QIcon()
        icon2.addFile(u":/images/icons/zoom_in.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_zoom_in.setIcon(icon2)
        self.action_zoom_in.setMenuRole(QAction.NoRole)
        self.action_zoom_out = QAction(MainWindow)
        self.action_zoom_out.setObjectName(u"action_zoom_out")
        icon3 = QIcon()
        icon3.addFile(u":/images/icons/zoom_out.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_zoom_out.setIcon(icon3)
        self.action_zoom_out.setMenuRole(QAction.NoRole)
        self.action_global = QAction(MainWindow)
        self.action_global.setObjectName(u"action_global")
        self.action_global.setCheckable(True)
        icon4 = QIcon()
        icon4.addFile(u":/images/icons/global.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_global.setIcon(icon4)
        self.action_global.setMenuRole(QAction.NoRole)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.frame_1 = QFrame(self.splitter)
        self.frame_1.setObjectName(u"frame_1")
        self.frame_1.setMinimumSize(QSize(0, 0))
        self.frame_1.setFrameShape(QFrame.StyledPanel)
        self.frame_1.setFrameShadow(QFrame.Raised)
        self.gridLayout = QGridLayout(self.frame_1)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, -1, 0, 0)
        self.tab_widget = QTabWidget(self.frame_1)
        self.tab_widget.setObjectName(u"tab_widget")
        self.tab_raw = QWidget()
        self.tab_raw.setObjectName(u"tab_raw")
        self.gridLayout_5 = QGridLayout(self.tab_raw)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.scroll_area_raw = QScrollArea(self.tab_raw)
        self.scroll_area_raw.setObjectName(u"scroll_area_raw")
        self.scroll_area_raw.setWidgetResizable(True)
        self.scroll_area_raw_contents = QWidget()
        self.scroll_area_raw_contents.setObjectName(u"scroll_area_raw_contents")
        self.scroll_area_raw_contents.setGeometry(QRect(0, 0, 319, 409))
        self.verticalLayout_4 = QVBoxLayout(self.scroll_area_raw_contents)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.scroll_area_raw.setWidget(self.scroll_area_raw_contents)

        self.gridLayout_5.addWidget(self.scroll_area_raw, 0, 0, 1, 1)

        self.tab_widget.addTab(self.tab_raw, "")
        self.tab_iso = QWidget()
        self.tab_iso.setObjectName(u"tab_iso")
        self.gridLayout_3 = QGridLayout(self.tab_iso)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.scroll_area_iso = QScrollArea(self.tab_iso)
        self.scroll_area_iso.setObjectName(u"scroll_area_iso")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_area_iso.sizePolicy().hasHeightForWidth())
        self.scroll_area_iso.setSizePolicy(sizePolicy)
        self.scroll_area_iso.setMinimumSize(QSize(0, 0))
        self.scroll_area_iso.setWidgetResizable(True)
        self.scroll_area_iso_contents = QWidget()
        self.scroll_area_iso_contents.setObjectName(u"scroll_area_iso_contents")
        self.scroll_area_iso_contents.setGeometry(QRect(0, 0, 319, 409))
        self.verticalLayout_2 = QVBoxLayout(self.scroll_area_iso_contents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.scroll_area_iso.setWidget(self.scroll_area_iso_contents)

        self.gridLayout_3.addWidget(self.scroll_area_iso, 0, 0, 1, 1)

        self.tab_widget.addTab(self.tab_iso, "")
        self.tab_quant = QWidget()
        self.tab_quant.setObjectName(u"tab_quant")
        self.gridLayout_4 = QGridLayout(self.tab_quant)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.scroll_area_quant = QScrollArea(self.tab_quant)
        self.scroll_area_quant.setObjectName(u"scroll_area_quant")
        self.scroll_area_quant.setWidgetResizable(True)
        self.scroll_area_quant_contents = QWidget()
        self.scroll_area_quant_contents.setObjectName(u"scroll_area_quant_contents")
        self.scroll_area_quant_contents.setGeometry(QRect(0, 0, 319, 409))
        self.verticalLayout_3 = QVBoxLayout(self.scroll_area_quant_contents)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.scroll_area_quant.setWidget(self.scroll_area_quant_contents)

        self.gridLayout_4.addWidget(self.scroll_area_quant, 0, 0, 1, 1)

        self.tab_widget.addTab(self.tab_quant, "")

        self.gridLayout.addWidget(self.tab_widget, 0, 0, 1, 1)

        self.splitter.addWidget(self.frame_1)
        self.frame_2 = QFrame(self.splitter)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy1)
        self.frame_2.setMaximumSize(QSize(400, 16777215))
        self.frame_2.setBaseSize(QSize(0, 0))
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.frame_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.species_table = QTableView(self.frame_2)
        self.species_table.setObjectName(u"species_table")
        self.species_table.setBaseSize(QSize(0, 0))
        self.species_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.species_table.setTabKeyNavigation(False)
        self.species_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.species_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout.addWidget(self.species_table)

        self.splitter.addWidget(self.frame_2)

        self.horizontalLayout.addWidget(self.splitter)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 37))
        self.menu_file = QMenu(self.menubar)
        self.menu_file.setObjectName(u"menu_file")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setIconSize(QSize(20, 20))
        MainWindow.addToolBar(Qt.TopToolBarArea, self.toolBar)

        self.menubar.addAction(self.menu_file.menuAction())
        self.menu_file.addAction(self.action_open_imzml_dialog)
        self.menu_file.addAction(self.action_save_images)
        self.toolBar.addAction(self.action_open_imzml_dialog)
        self.toolBar.addAction(self.action_save_images)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_zoom_out)
        self.toolBar.addAction(self.action_zoom_in)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_global)

        self.retranslateUi(MainWindow)

        self.tab_widget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.action_open_imzml_dialog.setText(QCoreApplication.translate("MainWindow", u"Open imzML file...", None))
        self.action_save_images.setText(QCoreApplication.translate("MainWindow", u"Save images...", None))
        self.action_zoom_in.setText(QCoreApplication.translate("MainWindow", u"action_zoom_in", None))
#if QT_CONFIG(tooltip)
        self.action_zoom_in.setToolTip(QCoreApplication.translate("MainWindow", u"Zoom in", None))
#endif // QT_CONFIG(tooltip)
        self.action_zoom_out.setText(QCoreApplication.translate("MainWindow", u"action_zoom_out", None))
#if QT_CONFIG(tooltip)
        self.action_zoom_out.setToolTip(QCoreApplication.translate("MainWindow", u"Zoom out", None))
#endif // QT_CONFIG(tooltip)
        self.action_global.setText(QCoreApplication.translate("MainWindow", u"global", None))
#if QT_CONFIG(tooltip)
        self.action_global.setToolTip(QCoreApplication.translate("MainWindow", u"Set quantitation scale globally across all images.", None))
#endif // QT_CONFIG(tooltip)
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_raw), QCoreApplication.translate("MainWindow", u"Raw", None))
#if QT_CONFIG(tooltip)
        self.tab_widget.setTabToolTip(self.tab_widget.indexOf(self.tab_raw), QCoreApplication.translate("MainWindow", u"Raw images", None))
#endif // QT_CONFIG(tooltip)
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_iso), QCoreApplication.translate("MainWindow", u"Iso", None))
#if QT_CONFIG(tooltip)
        self.tab_widget.setTabToolTip(self.tab_widget.indexOf(self.tab_iso), QCoreApplication.translate("MainWindow", u"Isotope corrected images", None))
#endif // QT_CONFIG(tooltip)
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_quant), QCoreApplication.translate("MainWindow", u"Quant", None))
#if QT_CONFIG(tooltip)
        self.tab_widget.setTabToolTip(self.tab_widget.indexOf(self.tab_quant), QCoreApplication.translate("MainWindow", u"Quantified images", None))
#endif // QT_CONFIG(tooltip)
        self.menu_file.setTitle(QCoreApplication.translate("MainWindow", u"&File", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar", None))
    # retranslateUi

