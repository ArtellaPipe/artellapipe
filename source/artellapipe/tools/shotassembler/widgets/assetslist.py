#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget implementation for assets list
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *


from tpQtLib.widgets import splitters


class ShotAssets(QWidget, object):

    updateHierarchy = Signal(QObject)

    def __init__(self, project, parent=None):

        self._project = project
        self.widgets = list()

        super(ShotAssets, self).__init__(parent=parent)

        self._update_menu()

    def ui(self):
        super(ShotAssets, self).ui()

        self.setMouseTracking(True)

        self._add_btn = QPushButton('Add Asset File')
        self.main_layout.addWidget(self._add_btn)
        self.main_layout.addLayout(splitters.SplitterLayout())
        self._assets_menu = QMenu()
        self._add_btn.setMenu(self._assets_menu)

        self._grid_layout = QGridLayout()
        self._grid_layout.setSpacing(2)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self._grid_layout)

        scroll_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet('QScrollArea { background-color: rgb(57,57,57);}')
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidget(scroll_widget)

        self._assets_layout = QVBoxLayout()
        self._assets_layout.setContentsMargins(1, 1, 1, 1)
        self._assets_layout.setSpacing(0)
        self._assets_layout.addStretch()
        scroll_widget.setLayout(self._assets_layout)
        self._grid_layout.addWidget(scroll_area, 1, 0, 1, 4)

    def all_assets(self):
        all_assets = list()
        for i in range(self._assets_layout.count()):
            child = self._assets_layout.itemAt(i)
            if child.widget() is not None:
                all_assets.append(child.widget())

        return all_assets

    def clear_assets(self):
        del self.widgets[:]
        while self._assets_layout.count():
            child = self._assets_layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()

        self._assets_layout.setSpacing(0)
        self._assets_layout.addStretch()

    def add_asset(self, asset):
        self.widgets.append(asset)
        self._assets_layout.insertWidget(0, asset)
        self.updateHierarchy.emit(asset)

    def _update_menu(self):
        pass
        # add_layout_action = QAction('Layout', self._assets_menu)
        # add_anim_action = QAction('Animation', self._assets_menu)
        # add_fx_action = QAction('FX', self._assets_menu)
        # add_light_action = QAction('Lighting', self._assets_menu)
        # for action in [add_layout_action, add_anim_action, add_fx_action, add_light_action]:
        #     self._assets_menu.addAction(action)
        #
        # add_layout_action.triggered.connect(self._on_add_layout)
        # add_anim_action.triggered.connect(self._on_add_animation)
        # add_fx_action.triggered.connect(self._on_add_fx)
        # add_light_action.triggered.connect(self._on_add_lighting)
