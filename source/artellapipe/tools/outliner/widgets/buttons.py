#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains item buttons for Outliner
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from artellapipe.tools.outliner.core import buttons

from Qt.QtWidgets import *


class ModelDisplayButtons(buttons.DisplayButtonsWidget, object):
    def __init__(self, parent=None):
        super(ModelDisplayButtons, self).__init__(parent=parent)

    def custom_ui(self):
        self.setMinimumWidth(25)

        self.proxy_hires_cbx = QComboBox()
        self.proxy_hires_cbx.addItem('proxy')
        self.proxy_hires_cbx.addItem('hires')
        self.proxy_hires_cbx.addItem('both')
        self.main_layout.addWidget(self.proxy_hires_cbx)


class ArtellaDisplayButtons(buttons.DisplayButtonsWidget, object):
    def __init__(self, parent=None):
        super(ArtellaDisplayButtons, self).__init__(parent=parent)

    def custom_ui(self):
        self.setMinimumWidth(25)
