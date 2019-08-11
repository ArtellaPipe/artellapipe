#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains settings widget for Solstice Outliner
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpQtLib.core import base

import artellapipe


class ArtellaOutlinerSettings(base.BaseWidget, object):

    settingsSaved = Signal()

    def __init__(self, parent=None):
        super(ArtellaOutlinerSettings, self).__init__(parent=parent)

    def ui(self):
        super(ArtellaOutlinerSettings, self).ui()

        self.save_btn = QPushButton('Save')
        self.save_btn.setIcon(artellapipe.solstice.resource.icon('save'))
        self.main_layout.addWidget(self.save_btn)

    def setup_signals(self):
        self.save_btn.clicked.connect(self.settingsSaved.emit)
