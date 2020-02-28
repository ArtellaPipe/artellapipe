#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for different types of buttons
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *

from tpDcc.libs.qt.widgets import buttons


class IconButton(buttons.BaseButton, object):
    """
    Class to create simple buttons with icons during normal state and hover state
    """

    def __init__(self, icon, button_text='', icon_padding=0, icon_min_size=8, icon_hover=None, parent=None):
        super(IconButton, self).__init__(parent=parent)

        self._pad = icon_padding
        self._minSize = icon_min_size
        self.setText(button_text)

        self._icon = icon
        self._icon_hover = icon_hover

        self.setFlat(True)
        self.setIcon(self._icon)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

    def enterEvent(self, event):
        if self._icon_hover:
            self.setIcon(self._icon_hover)

    def leaveEvent(self, event):
        self.setIcon(self._icon)
