#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base wrapper classes to create DCC dialogs
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc


class ArtellaDialog(tpDcc.Dialog, object):

    def __init__(
            self,
            project=None,
            tool=None,
            name='ArtellaDialog',
            title='Artella - Dialog',
            show_dragger=True, size=(200, 125),
            fixed_size=False,
            parent=None):

        self._project = project
        self._tool = tool

        title_pixmap = tpDcc.ResourcesMgr().pixmap(name='artella_title', extension='png')

        super(ArtellaDialog, self).__init__(
            name=name,
            title=title,
            parent=parent,
            show_dragger=show_dragger,
            size=size,
            fixed_size=fixed_size,
            title_pixmap=title_pixmap
        )

    @property
    def project(self):
        """
        Returns Artella project this window is linked to
        :return: ArtellaProject
        """

        return self._project

    def ui(self):
        super(ArtellaDialog, self).ui()

        dialog_icon = self._get_icon()
        self.setWindowIcon(dialog_icon)

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.main_layout.insertLayout(0, title_layout)

        title_background_pixmap = self._get_title_pixmap()
        self._logo_scene.addPixmap(title_background_pixmap)
        title_layout.addWidget(self.logo_view)

        # if not self._status_bar.has_url():
        #     self._status_bar.hide_info()

        if self._tool:
            self.main_layout.addWidget(self._tool)

        if self._project.is_dev():
            int_colors = self._project.dev_color0.split(',')
            dev_style = "background-color: rgb({}, {}, {})".format(
                int_colors[0], int_colors[1], int_colors[2], 255)
            self._dragger.setStyleSheet(dev_style)

    def setWindowTitle(self, title):
        if self._project.is_dev():
            title = '{} - [{}]'.format(title, self._project.get_environment())

        super(ArtellaDialog, self).setWindowTitle(title)

    def add_logo(self, logo_pixmap, offset_x, offset_y):
        """
        Adds a new logo into the title with the given offset
        :param logo_pixmap: QPixmap
        :param offset_x: int
        :param offset_y: int
        """

        win_logo = self._logo_scene.addPixmap(logo_pixmap)
        win_logo.setOffset(offset_x, offset_y)

    def _get_icon(self):
        """
        Internal function that returns the icon used for the window
        :return: QIcon
        """

        if self._project:
            window_icon = self._project.icon
            if not window_icon.isNull():
                return window_icon
            else:
                self._project.logger.warning(
                    '{} Project Icon not found: {}!'.format(
                        self._project.name.title(), self._project.icon_name + '.png'))

        return tpDcc.ResourcesMgr().icon('artella')

    def _get_title_pixmap(self):
        """
        Internal function that sets the pixmap used for the title
        """

        if self._project:
            title_background = self._project.config.get('title_background')
            title_pixmap = tpDcc.ResourcesMgr().pixmap(name=title_background, extension='png')
            if not title_pixmap.isNull():
                return title_pixmap
            else:
                self._project.logger.warning(
                    '{} Project Title Background image not found: {}!'.format(
                        self._project.name.title(), title_background + '.png'))

        return tpDcc.ResourcesMgr().pixmap(name='title_background', extension='png')
