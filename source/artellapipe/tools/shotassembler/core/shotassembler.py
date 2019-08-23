#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to export shot files to be used in the shot builder tool
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *
from Qt.QtCore import *

import tpQtLib
from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.gui import window
from artellapipe.tools.shotassembler.widgets import shothierarchy, shotproperties, assetslist, assetproperties, shotoverrides


class ShotAssembler(window.ArtellaWindow, object):

    VERSION = '0.0.1'
    LOGO_NAME = 'shotassembler_logo'

    def __init__(self, project):
        super(ShotAssembler, self).__init__(
            project=project,
            name='ShotAssembler',
            title='Shot Assembler',
            size=(900, 850)
        )

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def ui(self):
        super(ShotAssembler, self).ui()

        self._setup_menubar()

        self._dock_window = tpQtLib.DockWindow(use_scrollbar=True)
        self._dock_window.centralWidget().show()

        self._shots_props = shotproperties.ShotProps()
        self._shot_hierarchy = shothierarchy.ShotHierarchy()
        self._shot_assets = assetslist.ShotAssets(project=self._project)
        self._assets_props = assetproperties.AssetPropetiesEditor()
        self._shot_overrides = shotoverrides.ShotOverrides()

        self._generate_btn = QPushButton('GENERATE SHOT')
        self._generate_btn.setIcon(artellapipe.resource.icon('magic'))
        self._generate_btn.setMinimumHeight(30)
        self._generate_btn.setMinimumWidth(80)

        self.main_layout.addWidget(self._shots_props)
        self.main_layout.addLayout(splitters.SplitterLayout())
        self.main_layout.addWidget(self._dock_window)
        self._dock_window.main_layout.addWidget(self._shot_hierarchy)
        self._shot_assets_dock = self._dock_window.add_dock(widget=self._shot_assets, name='Assets', pos=Qt.LeftDockWidgetArea)
        self._asset_props_dock = self._dock_window.add_dock(widget=self._assets_props, name='Properties', tabify=False, pos=Qt.RightDockWidgetArea)
        self._shot_overrides_dock = self._dock_window.add_dock(widget=self._shot_overrides, name='Overrides', pos=Qt.RightDockWidgetArea)
        self.main_layout.addLayout(splitters.SplitterLayout())
        self.main_layout.addWidget(self._generate_btn)

    def _setup_menubar(self):
        """
        Internal callback function that setups menu bar
        :return: QMenuBar
        """

        menubar_widget = QWidget()
        menubar_layout = QVBoxLayout()
        menubar_layout.setContentsMargins(0, 0, 0, 0)
        menubar_layout.setSpacing(0)
        menubar_widget.setLayout(menubar_layout)
        menubar = QMenuBar()
        load_icon = artellapipe.resource.icon('open')
        save_icon = artellapipe.resource.icon('save')
        file_menu = menubar.addMenu('File')
        self.load_action = QAction(load_icon, 'Load', menubar_widget)
        self.save_action = QAction(save_icon, 'Save', menubar_widget)
        file_menu.addAction(self.load_action)
        file_menu.addAction(self.save_action)
        menubar_layout.addWidget(menubar)
        self.main_layout.addWidget(menubar_widget)

        return menubar



def run(project):
    win = ShotAssembler(project=project)
    win.show()

    return win
