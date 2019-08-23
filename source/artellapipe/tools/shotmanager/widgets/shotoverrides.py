#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for asset overrides widget
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *
from Qt.QtCore import *

from tpQtLib.core import base
from tpQtLib.widgets import splitters

import artellapipe


class ShotOverrides(base.BaseWidget, object):
    def __init__(self, parent=None):

        self._overrides = list()

        super(ShotOverrides, self).__init__(parent=parent)

        self._update_menu()

    def ui(self):
        super(ShotOverrides, self).ui()

        self.setMouseTracking(True)

        self._add_btn = QPushButton('Add Override')
        self._add_btn.setIcon(artellapipe.resource.icon('add'))
        self.main_layout.addWidget(self._add_btn)
        self.main_layout.addLayout(splitters.SplitterLayout())
        self._overrides_menu = QMenu()
        self._add_btn.setMenu(self._overrides_menu)

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

    def set_overrides(self, overrides):
        """
        self._setup_menubar()
        :param overrides: list
        :return:
        """

        self._overrides = overrides
        print('Overrides: {}'.format(overrides))

    def _update_menu(self):
        pass
        # add_property_override = QAction('Property', self._overrides_menu)
        # add_shader_override = QAction('Shader', self._overrides_menu)
        # add_shader_property_override = QAction('Shader Property', self._overrides_menu)
        # add_box_bbox = QAction('Box Bounding Box', self._overrides_menu)
        # for action in [add_property_override, add_shader_override, add_shader_property_override, add_box_bbox]:
        #     self._overrides_menu.addAction(action)
        #
        # add_property_override.triggered.connect(self._on_add_property_override)
        # add_shader_override.triggered.connect(self._on_add_shader_override)
        # add_shader_property_override.triggered.connect(self._on_add_shader_property_override)
        # add_box_bbox.triggered.connect(self._on_add_area_curve_override)
