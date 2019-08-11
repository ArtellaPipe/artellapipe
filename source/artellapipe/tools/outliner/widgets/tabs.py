#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tabs widgets for Solstice Outliner
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *

from tpQtLib.core import base

from solstice.pipeline.tools.outliner.widgets import outliners


class SolsticeTabs(base.BaseWidget, object):
    def __init__(self, parent=None):
        super(SolsticeTabs, self).__init__(parent=parent)

    def ui(self):
        super(SolsticeTabs, self).ui()

        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self.assets_outliner = outliners.SolsticeAssetsOutliner()
        self.characters_outliner = outliners.SolsticeCharactersOutliner()
        self.lights_outliner = outliners.SolsticeLightsOutliner()
        self.fx_outliner = outliners.SolsticeFXOutliner()
        self.cameras_outliner = outliners.SolsticeCamerasOutliner()

        self.tab_widget.addTab(self.assets_outliner, 'Assets')
        self.tab_widget.addTab(self.characters_outliner, 'Characters')
        self.tab_widget.addTab(self.lights_outliner, 'Lights')
        self.tab_widget.addTab(self.fx_outliner, 'FX')
        self.tab_widget.addTab(self.cameras_outliner, 'Cameras')

    def setup_signals(self):
        pass

    def get_count(self):
        return self.tab_widget.count()

    def get_widget(self, index):
        return self.tab_widget.widget(index)
