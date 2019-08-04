#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains definitions for asset in Artella
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpQtLib.core import base

import artellapipe
from artellapipe.core import abstract


class ArtellaAsset(abstract.AbstractAsset, object):
    def __init__(self, asset_data):
        super(ArtellaAsset, self).__init__()

        self._asset_data = asset_data

    def get_name(self):
        """
        Implements abstract get_name function
        Returns the name of the asset
        :return: str
        """

        return 'New Asset'

    def sync(self):
        """
        Syncrhonizes asset in Artella
        """

        pass


class ArtellaAssetWidget(base.BaseWidget, object):

    clicked = Signal(object)

    def __init__(self, asset, parent=None):

        self._asset = asset

        super(ArtellaAssetWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)
        return main_layout

    def ui(self):
        super(ArtellaAssetWidget, self).ui()

        self.setFixedWidth(160)
        self.setFixedHeight(160)

        widget_layout = QVBoxLayout()
        widget_layout.setContentsMargins(2, 2, 2, 2)
        widget_layout.setSpacing(0)
        main_frame = QFrame()
        main_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        main_frame.setLineWidth(1)
        main_frame.setLayout(widget_layout)
        self.main_layout.addWidget(main_frame)

        self._asset_btn = QPushButton('', self)
        self._asset_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._asset_btn.setIconSize(QSize(150, 150))
        self._asset_lbl = QLabel(self.get_name())
        self._asset_lbl.setAlignment(Qt.AlignCenter)

        widget_layout.addWidget(self._asset_btn)
        widget_layout.addWidget(self._asset_lbl)

    def setup_signals(self):
        self._asset_btn.clicked.connect(partial(self.clicked.emit, self))

    def get_name(self):
        """
        Returns name of the asset
        :return: str
        """

        return self._asset.get_name()

    def get_thumbnail_path(self):
        """
        Returns path where asset thumbnail is located
        :return: str
        """

        return ''

    def get_default_thumbnail_icon(self):
        """
        Returns the default thumbnail icon
        :return: QIcon
        """

        return artellapipe.resource.icon('default')

    def get_thumbnail_icon(self):
        """
        Returns thumbnail icon of the item
        """

        return QIcon()
