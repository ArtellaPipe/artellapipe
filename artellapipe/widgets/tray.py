#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom tray balloon widget
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging

from Qt.QtWidgets import *

from tpDcc.libs.qt.core import base

LOGGER = logging.getLogger('artellapipe')


class ArtellaTray(base.BaseWidget, object):

    ICON_NAME = None

    def __init__(self, project, parent=None):

        self._project = project

        super(ArtellaTray, self).__init__(parent=parent)

    def ui(self):
        super(ArtellaTray, self).ui()

        self._tray_icon = self._project.tray_icon

        tray_menu = self.create_menu()

        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip(self._project.name.title())
        self._tray.setIcon(self._tray_icon)
        self._tray.setContextMenu(tray_menu)

        if not QSystemTrayIcon.isSystemTrayAvailable():
            LOGGER.error('Tray Icon is not available!')
            return

        if not self._project.is_dev():
            self._tray.show()

    @property
    def project(self):
        """
        Returns project linked to this tray
        :return: ArtellaProject
        """

        return self._project

    def create_menu(self):
        """
        Creates menu used by the tray
        Overrides in child classes to create custom menus
        :return: QMenu
        """

        return QMenu(self)

    def show_message(self, title, msg):
        """
        Shows a message in the tray
        :param title: str
        :param msg: str
        """

        try:
            self._tray.showMessage(title, msg, self._tray_icon)
        except Exception:
            self._tray.showMessage(title, msg)
