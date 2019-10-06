#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget for progress bar
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


from Qt.QtCore import *
from Qt.QtWidgets import *

from tpQtLib.core import base


class ArtellaProgressBar(base.BaseWidget, object):
    def __init__(self, project, parent=None):

        self._project = project

        super(ArtellaProgressBar, self).__init__(parent=parent)

    def ui(self):
        super(ArtellaProgressBar, self).ui()

        self._progress_lbl = QLabel('')
        self._progress_lbl.setAlignment(Qt.AlignCenter)
        gradient_color_0 = self._project.progress_bar_color_0
        gradient_color_1 = self._project.progress_bar_color_1
        self._progress = QProgressBar()
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(
            "QProgressBar {border: 0px solid grey; border-radius:4px; padding:0px} QProgressBar::chunk"
            " {background: qlineargradient(x1: 0, y1: 1, x2: 1, y2: 1, stop: 0 "
            "rgb(" + gradient_color_0 + "), stop: 1 rgb(" + gradient_color_1 + ")); }")

        self.main_layout.addWidget(self._progress)
        self.main_layout.addWidget(self._progress_lbl)

    def set_minimum(self, min_value):
        """
        Sets the minimum value of the progress bar
        :param min_value: int
        """

        self._progress.setMinimum(min_value)

    def set_maximum(self, max_value):
        """
        Sets the maximum value of the progress bar
        :param max_value: int
        """

        self._progress.setMaximum(max_value)

    def value(self):
        """
        Returns vaue of the progress bar
        :return: float
        """

        return self._progress.value()

    def set_value(self, value):
        """
        Sets the value of the progress bar
        :param value: int
        """

        self._progress.setValue(value)

    def set_text(self, text):
        """
        Sets the progress text
        :param text: str
        """

        self._progress_lbl.setText(text)
