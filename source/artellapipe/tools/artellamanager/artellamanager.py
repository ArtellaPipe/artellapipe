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
from artellapipe.tools.artellamanager.widgets import userinfo, assetswidget


class ArtellaManager(window.ArtellaWindow, object):

    LOGO_NAME = 'manager_logo'
    USER_INFO_CLASS = userinfo.UserInfo

    def __init__(self, project):
        super(ArtellaManager, self).__init__(
            project=project,
            name='ManagerWindow',
            title='Manager',
            size=(1100, 900)
        )

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def ui(self):
        super(ArtellaManager, self).ui()

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

        # Create main slack widget
        self._stack = stack.SlidingStackedWidget(parent=self)

        # Add tabs and its categories (Assets, Shots, etc)
        self._tab_widget = QTabWidget()
        self._tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tab_widget.setMinimumHeight(330)
        self._stack.addWidget(self._tab_widget)

        assets_widget = assetswidget.AssetsWidget(project=self._project)

        sequences_widget = QWidget()
        sequences_layout = QVBoxLayout()
        sequences_layout.setContentsMargins(0, 0, 0, 0)
        sequences_layout.setSpacing(0)
        sequences_widget.setLayout(sequences_layout)

        self._tab_widget.addTab(assets_widget, 'Assets')
        self._tab_widget.addTab(sequences_widget, 'Sequences')
        self._tab_widget.setTabEnabled(1, False)

        # ============================================================================================

        self.main_layout.addWidget(self._stack)

    def setup_signals(self):
        self._project_artella_btn.clicked.connect(self._on_open_project_in_artella)
        self._project_folder_btn.clicked.connect(self._on_open_project_folder)

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


def run(project):
    win = ArtellaManager(project=project)
    win.show()

    return win
