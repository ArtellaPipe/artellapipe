#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget implementation that shows user info
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *


class UserInfo(QFrame, object):
    def __init__(self, project, parent=None):

        self._project = project

        super(UserInfo, self).__init__(parent)

        # self.setFixedHeight(25)

        self.main_layout = QHBoxLayout()
        self.main_layout.setAlignment(Qt.AlignTop)
        self.main_layout.setContentsMargins(3, 3, 3, 3)
        self.main_layout.setSpacing(2)
        self.setLayout(self.main_layout)

        self.setFrameShape(QFrame.Panel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)
