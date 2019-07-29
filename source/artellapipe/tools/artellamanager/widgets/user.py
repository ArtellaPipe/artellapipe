#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains a widget to show Artella user info for ArtellaManager
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import getpass

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import artellapipe
from artellapipe.utils import worker


class ArtellaUserInfoWidget(QWidget, object):

    availabilityUpdated = Signal(bool)

    def __init__(self, parent=None):
        self._user_pixmap = artellapipe.resource.pixmap(name='no_user', category='images', extension='png')
        self._user_name = getpass.getuser()

        super(ArtellaUserInfoWidget, self).__init__(parent=parent)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self._worker = worker.Worker(app=QApplication.instance())
        self._worker.workCompleted.connect(self._on_worker_completed)
        self._worker.workFailure.connect(self._on_worker_failure)
        self._worker.start()

        self._artella_color = QColor(255, 255, 0, 255)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_check_artella_avilability)
        self._start_check()

        self.setAttribute(Qt.WA_DeleteOnClose)

    def destroy(self):
        """
        Overrides base QWidget destroy function
        """

        if self._timer:
            self._timer.stop()

    def hideEvent(self, event):
        """
        Overrides base QWidget hideEvent function
        """

        self._timer.stop()
        super(ArtellaUserInfoWidget, self).hideEvent(event)

    def closeEvent(self, event):
        """
        Overrides base QWidget closeEvent function
        """

        self._timer.stop()
        super(ArtellaUserInfoWidget, self).closeEvent(event)

    def paintEvent(self, event):
        """
        Overrides base QWidget paintEvent function
        """

        super(ArtellaUserInfoWidget, self).paintEvent(event)

        painter = QPainter(self)

        # Draw user image
        fixed_image = QImage(128, 128, QImage.Format_ARGB32_Premultiplied)
        fixed_image.fill(0)
        image_painter = QPainter(fixed_image)
        clip = QPainterPath()
        clip.addEllipse(32, 32, 90, 90)
        image_painter.setClipPath(clip)
        image_painter.drawPixmap(0, 0, 128, 128, self._user_pixmap)
        image_painter.end()

        # Draw Artella availability icon
        painter.setBrush(self._artella_color)
        painter.setPen(self._artella_color)
        painter.drawEllipse(122, 72, 6, 6)
        painter.end()

    def artella_is_available(self, data):
        """
        Returns whether Artella is available or not
        """

        # available = sp.artella_is_available()
        available = True
        if available:
            self._enable_artella()
        else:
            self._disable_artella()
        self.availabilityUpdated.emit(available)

    def _start_check(self):
        """
        Function that initializes timer
        """

        if not self._timer.isActive():
            self._timer.start(5000)

    def _enable_artella(self):
        """
        Internal function that enables Artella indicator
        """

        self._artella_color = QColor(0, 255, 0, 255)
        self.repaint()

    def _disable_artella(self):
        """
        Internal function that disables Artella indicator
        """

        self._artella_color = QColor(255, 0, 0, 255)
        self.repaint()

    def _on_check_artella_avilability(self):
        """
        Internal callback function called by the timer to check Artella availability
        """

        self._worker_uid = self._worker.queue_work(self.artella_is_available, {})

    def _on_worker_completed(self, uid, data):
        """
        Internal callback function that is called when user worker is finished
        :param uid:
        :param data:
        """

        pass

    def _on_worker_failure(self, uid, msg):
        """
        Internal callback function that is called when the user worker fails
        :param uid:
        :param msg:
        """

        self._timer.stop()
        artellapipe.logger.error('Worker {} : {} has failed!'.format(uid, msg))
