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

from Qt.QtWidgets import *

from tpQtLib.core import base


class AssetInfoWidget(base.BaseWidget, object):
    def __init__(self, asset_widget, parent=None):

        self._asset_widget = asset_widget

        super(AssetInfoWidget, self).__init__(parent)

    def ui(self):
        super(AssetInfoWidget, self).ui()

        self.main_layout.addWidget(QPushButton('TEST'))

    def reset(self):
        """
        Restores initial values of the AssetInfoWidget
        """

        pass
