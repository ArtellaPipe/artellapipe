#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets to wait for Artella operations
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *

from artellapipe.widgets import spinner


class ArtellaWaiter(QFrame, object):
    def __init__(self, spinner_type=spinner.SpinnerType.Loading, parent=None):
        super(ArtellaWaiter, self).__init__(parent)

        self.setStyleSheet(
            "#background {border-radius: 3px;border-style: solid;border-width: 1px;border-color: rgb(32,32,32);}")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self.wait_spinner = spinner.WaitSpinner(spinner_type=spinner_type)
        self.wait_spinner._bg.setFrameShape(QFrame.NoFrame)
        self.wait_spinner._bg.setFrameShadow(QFrame.Plain)

        main_layout.addItem(QSpacerItem(0, 20, QSizePolicy.Fixed, QSizePolicy.Expanding))
        main_layout.addWidget(self.wait_spinner)
        main_layout.addItem(QSpacerItem(0, 20, QSizePolicy.Fixed, QSizePolicy.Expanding))
