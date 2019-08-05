#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that allow artists to interact with Artella functionality inside DCCS
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


from Qt.QtCore import *
from Qt.QtWidgets import *

from tpQtLib.widgets import stack

import artellapipe
from artellapipe.gui import window
from artellapipe.tools.assetsmanager.widgets import userinfo, assetswidget


class ArtellaAssetsManager(window.ArtellaWindow, object):

    LOGO_NAME = 'assetsmanager_logo'
    USER_INFO_CLASS = userinfo.UserInfo
    ASSET_WIDGET_CLASS = assetswidget.AssetsWidget

    def __init__(self, project, auto_start_assets_viewer=True):
        super(ArtellaAssetsManager, self).__init__(
            project=project,
            name='ManagerWindow',
            title='Manager',
            size=(1100, 900)
        )

        if auto_start_assets_viewer:
            self._assets_widget.update_assets()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def ui(self):
        super(ArtellaAssetsManager, self).ui()

        # Add User Info widget
        self._user_info = self.USER_INFO_CLASS()
        self.main_layout.addWidget(self._user_info)

        # Create Top Menu Bar
        self._menu_bar = self._setup_menubar()
        if not self._menu_bar:
            self._menu_bar = QMenuBar(self)
        self.main_layout.addWidget(self._menu_bar)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Raised)
        self.main_layout.addWidget(sep)

        self._main_stack = stack.SlidingStackedWidget(parent=self)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._attrs_stack = stack.SlidingStackedWidget(parent=self)

        no_items_widget = QFrame()
        no_items_widget.setFrameShape(QFrame.StyledPanel)
        no_items_widget.setFrameShadow(QFrame.Sunken)
        no_items_layout = QVBoxLayout()
        no_items_layout.setContentsMargins(0, 0, 0, 0)
        no_items_layout.setSpacing(0)
        no_items_widget.setLayout(no_items_layout)
        no_items_lbl = QLabel()
        no_items_pixmap = artellapipe.resource.pixmap('no_item_selected')
        no_items_lbl.setPixmap(no_items_pixmap)
        no_items_lbl.setAlignment(Qt.AlignCenter)
        no_items_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))
        no_items_layout.addWidget(no_items_lbl)
        no_items_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))

        self._tab_widget = QTabWidget()
        self._tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tab_widget.setMinimumHeight(330)

        self._assets_widget = self.ASSET_WIDGET_CLASS(project=self._project)

        sequences_widget = QWidget()
        sequences_layout = QVBoxLayout()
        sequences_layout.setContentsMargins(0, 0, 0, 0)
        sequences_layout.setSpacing(0)
        sequences_widget.setLayout(sequences_layout)

        self._tab_widget.addTab(self._assets_widget, 'Assets')
        self._tab_widget.addTab(sequences_widget, 'Sequences')
        self._tab_widget.setTabEnabled(1, False)

        self.main_layout.addWidget(self._main_stack)

        self._main_stack.addWidget(splitter)

        self._attrs_stack.addWidget(no_items_widget)

        splitter.addWidget(self._tab_widget)
        splitter.addWidget(self._attrs_stack)

    def setup_signals(self):
        self._project_artella_btn.clicked.connect(self._on_open_project_in_artella)
        self._project_folder_btn.clicked.connect(self._on_open_project_folder)
        self._assets_widget.assetAdded.connect(self._on_asset_added)

    def closeEvent(self, event):
        """
        Overrides base window.ArtellaWindow closeEvent function
        :param event: QEvent
        """

        self.save_settings()
        self.remove_callbacks()
        self.windowClosed.emit()
        event.accept()

    def _setup_menubar(self):
        """
        Internal function used to setup Artella Manager menu bar
        """

        menubar_widget = QWidget()
        menubar_layout = QGridLayout()
        menubar_layout.setAlignment(Qt.AlignTop)
        menubar_layout.setContentsMargins(0, 0, 0, 0)
        menubar_layout.setSpacing(2)
        menubar_widget.setLayout(menubar_layout)
        self._project_artella_btn = QToolButton()
        self._project_artella_btn.setText('Artella')
        self._project_artella_btn.setIcon(artellapipe.resource.icon('artella'))
        self._project_artella_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._project_folder_btn = QToolButton()
        self._project_folder_btn.setText('Project')
        self._project_folder_btn.setIcon(artellapipe.resource.icon('folder'))
        self._project_folder_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        synchronize_btn = QToolButton()
        synchronize_btn.setText('Synchronize')
        synchronize_btn.setPopupMode(QToolButton.InstantPopup)
        synchronize_btn.setIcon(artellapipe.resource.icon('sync'))
        synchronize_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        # settings_btn = QToolButton()
        # settings_btn.setText('Settings')
        # settings_btn.setIcon(artellapipe.resource.icon('settings'))
        # settings_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        for i, btn in enumerate([self._project_artella_btn, self._project_folder_btn, synchronize_btn]):
            menubar_layout.addWidget(btn, 0, i, 1, 1, Qt.AlignCenter)

        return menubar_widget

    def _setup_asset_signals(self, asset_widget):
        """
        Internal function that sets proper signals to given asset widget
        This function can be extended to add new signals to added items
        :param asset_widget: ArtellaAssetWidget
        """

        pass

    def _on_artella_not_available(self):
        """
        Internal callback function that is called by ArtellaUserInfo widget when Artella is not available
        TODO: If Artella is not enabled we should disable all the widget of the UI and notify the user
        """

        pass

    def _on_open_project_in_artella(self):
        """
        Internal callback function that is called when the user presses Artella menu bar button
        """

        if not self._project:
            return

        self._project.open_in_artella()

    def _on_open_project_folder(self):
        """
        Internal callback function that is called when the user presses Project menu bar button
        """

        if not self._project:
            return

        self._project.open_folder()

    def _on_asset_added(self, asset_widget):
        """
        Internal callback function that is called when a new asset widget is added to the assets viewer
        :param asset_widget: ArtellaAssetWidget
        """

        if not asset_widget:
            return

        self._setup_asset_signals(asset_widget)


def run(project):
    win = ArtellaAssetsManager(project=project)
    win.show()

    return win
