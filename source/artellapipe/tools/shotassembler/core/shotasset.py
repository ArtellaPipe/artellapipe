#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base definitions for ShotExporter asset items
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

from Qt.QtWidgets import *
from Qt.QtCore import *

from tpQtLib.core import base


class AbstractItemWidget(base.BaseWidget, object):
    def __init__(self, asset, parent=None):

        self.parent = parent
        self._asset = asset
        self._is_selectable = True
        self._is_selected = False

        super(AbstractItemWidget, self).__init__(parent)

    def ui(self):
        super(AbstractItemWidget, self).ui()

        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumHeight(35)
        self.setMaximumHeight(35)

        self._item_widget = QFrame()
        self._item_layout = QGridLayout()
        self._item_layout.setContentsMargins(0, 0, 0, 0)
        self._item_widget.setLayout(self._item_layout)
        self.main_layout.addWidget(self._item_widget)

    @property
    def asset(self):
        """
        Returns asset node wrapped by the item
        :return:
        """

        return self._asset

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._is_selected:
                self.deselect()
            else:
                self.select()
            self.clicked.emit(self, event)

    def select(self):
        if not self._is_selectable:
            return

        self._is_selected = True
        self._item_widget.setStyleSheet('QFrame { background-color: rgb(21,60,97);}')

    def deselect(self):
        if not self._is_selectable:
            return

        self._is_selected = False
        self._item_widget.setStyleSheet('QFrame { background-color: rgb(55,55,55);}')

    def set_select(self, select=False):
        if not self._is_selectable:
            return

        if select:
            self.select()
        else:
            self.deselect()

        return self._is_selected


class ShotAsset(AbstractItemWidget, object):
    clicked = Signal(QObject, QEvent)
    contextRequested = Signal(QObject, QAction)

    def __init__(self, asset, parent=None):
        super(ShotAsset, self).__init__(asset, parent)
        self.is_selectable = False

    def custom_ui(self):
        super(ShotAsset, self).custom_ui()

        self._item_widget.setFrameStyle(QFrame.Raised | QFrame.StyledPanel)
        self._item_widget.setStyleSheet('QFrame { background-color: rgb(55,55,55);}')

        self._asset_lbl = QLabel(os.path.basename(self._asset))
        self._asset_lbl.setToolTip(self._asset)
        self.item_layout.addWidget(self._asset_lbl, 0, 1, 1, 1)

        self._item_layout.setColumnStretch(1, 5)
        self._item_layout.setAlignment(Qt.AlignLeft)
