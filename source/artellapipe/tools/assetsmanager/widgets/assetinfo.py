#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget that shows asset information
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpQtLib.core import base
from tpQtLib.widgets import breadcrumb

import artellapipe


class AssetInfoWidget(base.BaseWidget, object):
    def __init__(self, asset_widget, parent=None):

        self._asset_widget = asset_widget

        super(AssetInfoWidget, self).__init__(parent)

        self._init()

    def ui(self):
        super(AssetInfoWidget, self).ui()

        self._title_breadcrumb = breadcrumb.BreadcrumbFrame()
        self._asset_icon_frame = QFrame()
        self._asset_icon_frame.setFrameShape(QFrame.StyledPanel)
        self._asset_icon_frame.setFrameShadow(QFrame.Sunken)
        self._asset_icon_frame.setLineWidth(3)
        self._asset_icon_frame.setStyleSheet('background-color: rgba(60, 60, 60, 100); border-radius:5px;')
        asset_icon_layout = QHBoxLayout()
        asset_icon_layout.setContentsMargins(0, 0, 0, 0)
        asset_icon_layout.setSpacing(0)
        self._asset_icon_frame.setLayout(asset_icon_layout)
        self._asset_icon_lbl = QLabel()
        self._asset_icon_lbl.setAlignment(Qt.AlignCenter)
        self._asset_icon_lbl.setPixmap(artellapipe.resource.pixmap('default'))
        asset_icon_layout.addWidget(self._asset_icon_lbl)

        self.main_layout.addWidget(self._title_breadcrumb)
        self.main_layout.addWidget(self._asset_icon_frame)

    def reset(self):
        """
        Restores initial values of the AssetInfoWidget
        """

        pass

    def _init(self):
        """
        Internal function that initializes asset info widget
        """

        if not self._asset_widget:
            return

        self._title_breadcrumb.set([self._asset_widget.asset.get_name()])
        self._asset_icon_lbl.setPixmap(QPixmap(self._asset_widget.asset.get_thumbnail_icon()).scaled(200, 200, Qt.KeepAspectRatio))
