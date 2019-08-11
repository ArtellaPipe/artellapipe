#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget buttons for Solstice Outliners
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *
from Qt.QtGui import *


class DisplayButtonsWidget(QWidget, object):
    def __init__(self, parent=None):
        super(DisplayButtonsWidget, self).__init__(parent)

        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.setMouseTracking(True)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(1)
        self.setLayout(self.main_layout)

        self.custom_ui()
        self.setup_signals()

    def custom_ui(self):
        pass

    def setup_signals(self):
        pass


class AssetDisplayButtons(DisplayButtonsWidget, object):

    def __init__(self, parent=None):
        super(AssetDisplayButtons, self).__init__(parent=parent)

    def custom_ui(self):

        self.setMinimumWidth(25)

        self.view_btn = QPushButton()
        self.view_btn.setIcon(QIcon(QPixmap(':/eye.png')))
        self.view_btn.setFlat(True)
        self.view_btn.setFixedWidth(25)
        self.view_btn.setCheckable(True)
        self.view_btn.setChecked(True)
        self.view_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.main_layout.addWidget(self.view_btn)
