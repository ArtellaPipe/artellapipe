#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget implementation for the shot hierarchy
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *
from Qt.QtCore import *

from tpQtLib.core import base


class ShotHierarchy(base.BaseWidget, object):

    updateProperties = Signal(QObject)
    refresh = Signal()

    def __init__(self, parent=None):

        self._widgets = list()

        super(ShotHierarchy, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        return main_layout

    def ui(self):
        super(ShotHierarchy, self).ui()

        self.setMouseTracking(True)

        self._grid_layout = QGridLayout()
        self._grid_layout.setSpacing(0)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self._grid_layout)

        scroll_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet('QScrollArea { background-color: rgb(57,57,57);}')
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidget(scroll_widget)

        self._hierarchy_layout = QVBoxLayout()
        self._hierarchy_layout.setContentsMargins(0, 0, 0, 0)
        self._hierarchy_layout.setSpacing(0)
        self._hierarchy_layout.addStretch()
        scroll_widget.setLayout(self._hierarchy_layout)
        self._grid_layout.addWidget(scroll_area, 1, 0, 1, 4)

    def all_hierarchy(self):
        all_hierarhcy = list()
        for i in range(self._hierarchy_layout.count()):
            child = self._hierarchy_layout.itemAt(i)
            if child.widget() is not None:
                all_hierarhcy.append(child.widget())

        return all_hierarhcy

    def clear_hierarchy(self):
        del self._widgets[:]
        while self._hierarchy_layout.count():
            child = self._hierarchy_layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()

        self._hierarchy_layout.setSpacing(0)
        self._hierarchy_layout.addStretch()

    def add_asset(self, asset):
        self._widgets.append(asset)
        self._hierarchy_layout.insertWidget(0, asset)
        asset.clicked.connect(self._on_item_clicked)

        return asset

    def _on_item_clicked(self, widget, event):
        if widget is None:
            self.updateProperties.emit(None)
            return
        else:
            for asset_widget in self._widgets:
                if asset_widget != widget:
                    asset_widget.deselect()
                else:
                    asset_widget.select()
            self.updateProperties.emit(widget)