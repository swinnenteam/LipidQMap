# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MsiMainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    QTime,
    QUrl,
)
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QGridLayout,
    QHeaderView,
    QMainWindow,
    QMenu,
    QMenuBar,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableView,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from . import resources_rc


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.action_open_imzml_dialog = QAction(MainWindow)
        self.action_open_imzml_dialog.setObjectName("action_open_imzml_dialog")
        icon = QIcon()
        icon.addFile(":/images/icons/open_file.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_open_imzml_dialog.setIcon(icon)
        self.action_open_save_dialog = QAction(MainWindow)
        self.action_open_save_dialog.setObjectName("action_open_save_dialog")
        icon1 = QIcon()
        icon1.addFile(":/images/icons/save.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_open_save_dialog.setIcon(icon1)
        self.action_zoom_in = QAction(MainWindow)
        self.action_zoom_in.setObjectName("action_zoom_in")
        icon2 = QIcon()
        icon2.addFile(":/images/icons/zoom_in.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_zoom_in.setIcon(icon2)
        self.action_zoom_in.setMenuRole(QAction.NoRole)
        self.action_zoom_out = QAction(MainWindow)
        self.action_zoom_out.setObjectName("action_zoom_out")
        icon3 = QIcon()
        icon3.addFile(":/images/icons/zoom_out.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_zoom_out.setIcon(icon3)
        self.action_zoom_out.setMenuRole(QAction.NoRole)
        self.action_global = QAction(MainWindow)
        self.action_global.setObjectName("action_global")
        self.action_global.setCheckable(True)
        icon4 = QIcon()
        icon4.addFile(":/images/icons/global.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_global.setIcon(icon4)
        self.action_global.setMenuRole(QAction.NoRole)
        self.action_rotate_left = QAction(MainWindow)
        self.action_rotate_left.setObjectName("action_rotate_left")
        icon5 = QIcon()
        icon5.addFile(":/images/icons/rotate_left.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_rotate_left.setIcon(icon5)
        self.action_rotate_left.setMenuRole(QAction.NoRole)
        self.action_rotate_right = QAction(MainWindow)
        self.action_rotate_right.setObjectName("action_rotate_right")
        icon6 = QIcon()
        icon6.addFile(":/images/icons/rotate_right.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_rotate_right.setIcon(icon6)
        self.action_rotate_right.setMenuRole(QAction.NoRole)
        self.action_reflect_horizontal = QAction(MainWindow)
        self.action_reflect_horizontal.setObjectName("action_reflect_horizontal")
        icon7 = QIcon()
        icon7.addFile(":/images/icons/reflect_horizontal.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_reflect_horizontal.setIcon(icon7)
        self.action_reflect_horizontal.setMenuRole(QAction.NoRole)
        self.action_reflect_vertical = QAction(MainWindow)
        self.action_reflect_vertical.setObjectName("action_reflect_vertical")
        icon8 = QIcon()
        icon8.addFile(":/images/icons/reflect_vertical.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_reflect_vertical.setIcon(icon8)
        self.action_reflect_vertical.setMenuRole(QAction.NoRole)
        self.action_open_about_dialog = QAction(MainWindow)
        self.action_open_about_dialog.setObjectName("action_open_about_dialog")
        icon9 = QIcon()
        icon9.addFile(":/images/icons/help.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_open_about_dialog.setIcon(icon9)
        self.action_open_about_dialog.setMenuRole(QAction.NoRole)
        self.action_open_settings_window = QAction(MainWindow)
        self.action_open_settings_window.setObjectName("action_open_settings_window")
        icon10 = QIcon()
        icon10.addFile(":/images/icons/settings.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_open_settings_window.setIcon(icon10)
        self.action_open_settings_window.setMenuRole(QAction.NoRole)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_7 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.splitter_charts = QSplitter(self.centralwidget)
        self.splitter_charts.setObjectName("splitter_charts")
        self.splitter_charts.setOrientation(Qt.Orientation.Vertical)
        self.splitter = QSplitter(self.splitter_charts)
        self.splitter.setObjectName("splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.frame_1 = QFrame(self.splitter)
        self.frame_1.setObjectName("frame_1")
        self.frame_1.setMinimumSize(QSize(0, 0))
        self.frame_1.setFrameShape(QFrame.StyledPanel)
        self.frame_1.setFrameShadow(QFrame.Raised)
        self.gridLayout = QGridLayout(self.frame_1)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout.setContentsMargins(0, -1, 0, 0)
        self.tab_widget = QTabWidget(self.frame_1)
        self.tab_widget.setObjectName("tab_widget")
        self.tab_raw = QWidget()
        self.tab_raw.setObjectName("tab_raw")
        self.gridLayout_5 = QGridLayout(self.tab_raw)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.scroll_area_raw = QScrollArea(self.tab_raw)
        self.scroll_area_raw.setObjectName("scroll_area_raw")
        self.scroll_area_raw.setWidgetResizable(True)
        self.scroll_area_raw_contents = QWidget()
        self.scroll_area_raw_contents.setObjectName("scroll_area_raw_contents")
        self.scroll_area_raw_contents.setGeometry(QRect(0, 0, 337, 319))
        self.verticalLayout_4 = QVBoxLayout(self.scroll_area_raw_contents)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.scroll_area_raw.setWidget(self.scroll_area_raw_contents)

        self.gridLayout_5.addWidget(self.scroll_area_raw, 0, 0, 1, 1)

        self.tab_widget.addTab(self.tab_raw, "")
        self.tab_iso = QWidget()
        self.tab_iso.setObjectName("tab_iso")
        self.gridLayout_3 = QGridLayout(self.tab_iso)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.scroll_area_iso = QScrollArea(self.tab_iso)
        self.scroll_area_iso.setObjectName("scroll_area_iso")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_area_iso.sizePolicy().hasHeightForWidth())
        self.scroll_area_iso.setSizePolicy(sizePolicy)
        self.scroll_area_iso.setMinimumSize(QSize(0, 0))
        self.scroll_area_iso.setWidgetResizable(True)
        self.scroll_area_iso_contents = QWidget()
        self.scroll_area_iso_contents.setObjectName("scroll_area_iso_contents")
        self.scroll_area_iso_contents.setGeometry(QRect(0, 0, 337, 319))
        self.verticalLayout_2 = QVBoxLayout(self.scroll_area_iso_contents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.scroll_area_iso.setWidget(self.scroll_area_iso_contents)

        self.gridLayout_3.addWidget(self.scroll_area_iso, 0, 0, 1, 1)

        self.tab_widget.addTab(self.tab_iso, "")
        self.tab_quant = QWidget()
        self.tab_quant.setObjectName("tab_quant")
        self.gridLayout_4 = QGridLayout(self.tab_quant)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.scroll_area_quant = QScrollArea(self.tab_quant)
        self.scroll_area_quant.setObjectName("scroll_area_quant")
        self.scroll_area_quant.setWidgetResizable(True)
        self.scroll_area_quant_contents = QWidget()
        self.scroll_area_quant_contents.setObjectName("scroll_area_quant_contents")
        self.scroll_area_quant_contents.setGeometry(QRect(0, 0, 337, 319))
        self.verticalLayout_3 = QVBoxLayout(self.scroll_area_quant_contents)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.scroll_area_quant.setWidget(self.scroll_area_quant_contents)

        self.gridLayout_4.addWidget(self.scroll_area_quant, 0, 0, 1, 1)

        self.tab_widget.addTab(self.tab_quant, "")

        self.gridLayout.addWidget(self.tab_widget, 0, 0, 1, 1)

        self.splitter.addWidget(self.frame_1)
        self.frame_2 = QFrame(self.splitter)
        self.frame_2.setObjectName("frame_2")
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
        self.verticalLayout.setObjectName("verticalLayout")
        self.species_table = QTableView(self.frame_2)
        self.species_table.setObjectName("species_table")
        self.species_table.setBaseSize(QSize(0, 0))
        self.species_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.species_table.setTabKeyNavigation(False)
        self.species_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.species_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout.addWidget(self.species_table)

        self.splitter.addWidget(self.frame_2)
        self.splitter_charts.addWidget(self.splitter)
        self.barplot_frame = QFrame(self.splitter_charts)
        self.barplot_frame.setObjectName("barplot_frame")
        self.barplot_frame.setFrameShape(QFrame.StyledPanel)
        self.barplot_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.barplot_frame)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.tab_widget_charts = QTabWidget(self.barplot_frame)
        self.tab_widget_charts.setObjectName("tab_widget_charts")
        self.tab_species_plot = QWidget()
        self.tab_species_plot.setObjectName("tab_species_plot")
        self.verticalLayout_6 = QVBoxLayout(self.tab_species_plot)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.tab_widget_charts.addTab(self.tab_species_plot, "")
        self.tab_mz_spectrum = QWidget()
        self.tab_mz_spectrum.setObjectName("tab_mz_spectrum")
        self.verticalLayout_8 = QVBoxLayout(self.tab_mz_spectrum)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.tab_widget_charts.addTab(self.tab_mz_spectrum, "")

        self.verticalLayout_5.addWidget(self.tab_widget_charts)

        self.splitter_charts.addWidget(self.barplot_frame)

        self.verticalLayout_7.addWidget(self.splitter_charts)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 37))
        self.menu_file = QMenu(self.menubar)
        self.menu_file.setObjectName("menu_file")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.menuSettings = QMenu(self.menubar)
        self.menuSettings.setObjectName("menuSettings")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setIconSize(QSize(20, 20))
        MainWindow.addToolBar(Qt.TopToolBarArea, self.toolBar)

        self.menubar.addAction(self.menu_file.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuSettings.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menu_file.addAction(self.action_open_imzml_dialog)
        self.menu_file.addAction(self.action_open_save_dialog)
        self.menuEdit.addAction(self.action_rotate_left)
        self.menuEdit.addAction(self.action_rotate_right)
        self.menuEdit.addAction(self.action_reflect_horizontal)
        self.menuEdit.addAction(self.action_reflect_vertical)
        self.menuHelp.addAction(self.action_open_about_dialog)
        self.menuSettings.addAction(self.action_open_settings_window)
        self.toolBar.addAction(self.action_open_imzml_dialog)
        self.toolBar.addAction(self.action_open_save_dialog)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_zoom_out)
        self.toolBar.addAction(self.action_zoom_in)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_rotate_left)
        self.toolBar.addAction(self.action_rotate_right)
        self.toolBar.addAction(self.action_reflect_horizontal)
        self.toolBar.addAction(self.action_reflect_vertical)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_global)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_open_settings_window)
        self.toolBar.addAction(self.action_open_about_dialog)

        self.retranslateUi(MainWindow)

        self.tab_widget.setCurrentIndex(1)
        self.tab_widget_charts.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        self.action_open_imzml_dialog.setText(
            QCoreApplication.translate("MainWindow", "Open imzML files...", None)
        )
        self.action_open_save_dialog.setText(
            QCoreApplication.translate("MainWindow", "Save images...", None)
        )
        self.action_zoom_in.setText(
            QCoreApplication.translate("MainWindow", "action_zoom_in", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_zoom_in.setToolTip(QCoreApplication.translate("MainWindow", "Zoom in", None))
        # endif // QT_CONFIG(tooltip)
        self.action_zoom_out.setText(
            QCoreApplication.translate("MainWindow", "action_zoom_out", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_zoom_out.setToolTip(QCoreApplication.translate("MainWindow", "Zoom out", None))
        # endif // QT_CONFIG(tooltip)
        self.action_global.setText(QCoreApplication.translate("MainWindow", "global", None))
        # if QT_CONFIG(tooltip)
        self.action_global.setToolTip(
            QCoreApplication.translate("MainWindow", "Global scale", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_rotate_left.setText(
            QCoreApplication.translate("MainWindow", "Rotate Left", None)
        )
        self.action_rotate_right.setText(
            QCoreApplication.translate("MainWindow", "Rotate Right", None)
        )
        self.action_reflect_horizontal.setText(
            QCoreApplication.translate("MainWindow", "Reflect Horizontal", None)
        )
        self.action_reflect_vertical.setText(
            QCoreApplication.translate("MainWindow", "Reflect Vertical", None)
        )
        self.action_open_about_dialog.setText(
            QCoreApplication.translate("MainWindow", "About", None)
        )
        self.action_open_settings_window.setText(
            QCoreApplication.translate("MainWindow", "Settings", None)
        )
        self.tab_widget.setTabText(
            self.tab_widget.indexOf(self.tab_raw),
            QCoreApplication.translate("MainWindow", "Raw", None),
        )
        # if QT_CONFIG(tooltip)
        self.tab_widget.setTabToolTip(
            self.tab_widget.indexOf(self.tab_raw),
            QCoreApplication.translate("MainWindow", "Raw images", None),
        )
        # endif // QT_CONFIG(tooltip)
        self.tab_widget.setTabText(
            self.tab_widget.indexOf(self.tab_iso),
            QCoreApplication.translate("MainWindow", "Isotope corrected", None),
        )
        # if QT_CONFIG(tooltip)
        self.tab_widget.setTabToolTip(
            self.tab_widget.indexOf(self.tab_iso),
            QCoreApplication.translate("MainWindow", "Isotope corrected images", None),
        )
        # endif // QT_CONFIG(tooltip)
        self.tab_widget.setTabText(
            self.tab_widget.indexOf(self.tab_quant),
            QCoreApplication.translate("MainWindow", "Quantitative", None),
        )
        # if QT_CONFIG(tooltip)
        self.tab_widget.setTabToolTip(
            self.tab_widget.indexOf(self.tab_quant),
            QCoreApplication.translate("MainWindow", "Quantified images", None),
        )
        # endif // QT_CONFIG(tooltip)
        self.tab_widget_charts.setTabText(
            self.tab_widget_charts.indexOf(self.tab_species_plot),
            QCoreApplication.translate("MainWindow", "Species plot", None),
        )
        self.tab_widget_charts.setTabText(
            self.tab_widget_charts.indexOf(self.tab_mz_spectrum),
            QCoreApplication.translate("MainWindow", "Mass spectrum", None),
        )
        self.menu_file.setTitle(QCoreApplication.translate("MainWindow", "&File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", "Edit", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", "Help", None))
        self.menuSettings.setTitle(QCoreApplication.translate("MainWindow", "Settings", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", "toolBar", None))

    # retranslateUi
