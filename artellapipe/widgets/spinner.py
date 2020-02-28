#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget to create wait spinners
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc

from artellapipe.widgets import label


class SpinnerType(object):
    Thumb = 'thumb'
    Circle = 'circle'
    Loading = 'loading'


class WaitSpinner(QWidget, object):

    EMPTY_FILE = 'empty_file'
    THUMB_INFO = (7, 'thumb_working_{}')
    LOADING_INFO = (7, 'thumb_loading_{}')
    CIRCLE_INFO = (10, 'circle_loading_{}')

    def __init__(self, spinner_type=SpinnerType.Thumb, parent=None):
        super(WaitSpinner, self).__init__(parent=parent)

        self._spin_icons = list()

        empty_thumb = tpDcc.ResourcesMgr().pixmap(self.EMPTY_FILE)

        if spinner_type == SpinnerType.Thumb:
            for i in range(self.THUMB_INFO[0]):
                self._spin_icons.append(
                    tpDcc.ResourcesMgr().pixmap(self.THUMB_INFO[1].format(i + 1)))
        elif spinner_type == SpinnerType.Loading:
            for i in range(self.LOADING_INFO[0]):
                self._spin_icons.append(
                    tpDcc.ResourcesMgr().pixmap(self.LOADING_INFO[1].format(i + 1)))
        else:
            for i in range(self.CIRCLE_INFO[0]):
                self._spin_icons.append(
                    tpDcc.ResourcesMgr().pixmap(self.CIRCLE_INFO[1].format(i + 1)))

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(2)
        self.setLayout(main_layout)

        self._bg = QFrame(self)
        self._bg.setStyleSheet(
            "#background {border-radius: 3px;border-style: solid;border-width: 1px;border-color: rgb(32,32,32);}")
        self._bg.setFrameShape(QFrame.StyledPanel)
        self._bg.setFrameShadow(QFrame.Raised)
        self.frame_layout = QHBoxLayout()
        self.frame_layout.setContentsMargins(4, 4, 4, 4)
        self._bg.setLayout(self.frame_layout)
        main_layout.addWidget(self._bg)

        self._thumb_lbl = label.ThumbnailLabel()
        self._thumb_lbl.setMinimumSize(QSize(80, 55))
        self._thumb_lbl.setMaximumSize(QSize(80, 55))
        self._thumb_lbl.setStyleSheet('')
        self._thumb_lbl.setPixmap(empty_thumb)
        self._thumb_lbl.setScaledContents(False)
        self._thumb_lbl.setAlignment(Qt.AlignCenter)
        self.frame_layout.addWidget(self._thumb_lbl)

        self._current_spinner_index = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_update_spinner)

    def showEvent(self, event):
        """
        Overrides base QWidget showEvent function
        :param event: QEvent
        """

        if not self._timer.isActive():
            self._timer.start(100)
        super(WaitSpinner, self).showEvent(event)

    def hideEvent(self, event):
        """
        Overrides base QWidget hideEvent function
        :param event: QEvent
        """

        self._timer.stop()
        super(WaitSpinner, self).hideEvent(event)

    def closeEvent(self, event):
        """
        Overrides base QWidget closeEvent function
        :param event: QEvent
        """

        self._timer.stop()
        super(WaitSpinner, self).closeEvent(event)

    def stop(self):
        """
        Stops spinner
        """

        self._timer.stop()

    def _on_update_spinner(self):
        """
        Internal callback function that is called by internal timer in a constant rate
        """

        # print('updating ...')
        self._thumb_lbl.setPixmap(self._spin_icons[self._current_spinner_index])
        self._current_spinner_index += 1
        if self._current_spinner_index == len(self._spin_icons):
            self._current_spinner_index = 0
