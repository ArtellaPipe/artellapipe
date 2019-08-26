#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget implementation for the shot properties
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import osplatform

from tpQtLib.widgets import splitters


class ShotImage(QWidget, object):
    def __init__(self, parent=None):
        super(ShotImage, self).__init__(parent=parent)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(2)
        self.setLayout(self.main_layout)

        self._icon_btn = QPushButton('Icon')
        self._icon_btn.setMinimumSize(QSize(80, 80))
        self._icon_btn.setMaximumSize(QSize(80, 80))
        self._icon_btn.setIconSize(QSize(80, 80))

        self.main_layout.addWidget(self._icon_btn)

    def save(self):
        pass

    def load(self):
        pass


class ShotProps(QFrame, object):
    def __init__(self, project, parent=None):

        self._project = project

        super(ShotProps, self).__init__(parent=parent)

        self.setMinimumHeight(80)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(2)
        self.setLayout(self.main_layout)

        self.shot_img = ShotImage()
        # self.shot_img.setPixmap(resource.pixmap('project_logo', category='images').scaled(QSize(125, 125), Qt.KeepAspectRatio))
        self.prop_lbl = splitters.Splitter(self._project.name.title())
        self.user_lbl = QLabel(osplatform.get_user())

        self.main_layout.addWidget(self.shot_img)
        self.main_layout.addWidget(splitters.get_horizontal_separator_widget())
        self.main_layout.addWidget(self.user_lbl)
        self.main_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))